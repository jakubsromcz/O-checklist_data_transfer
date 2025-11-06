from utils.role_filter import *
from core.permissions import *
from datetime import datetime, timezone as dt_timezone
from django.utils.dateparse import parse_datetime
import re
from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Race, OchecklistStore


class OchecklistAPIView(APIView):
    permission_classes = []

    def get(self, request):
        api_key = (request.headers.get('Key') or '').strip().lower() 
        qs = None

        if is_manager(request.user):
            qs = (OchecklistStore.objects
                  .select_related('race__event')
                  .order_by('-id')[:100])
        elif api_key:
            qs = (OchecklistStore.objects
                  .select_related('race__event')
                  .filter(racecieved_api_key=api_key)
                  .order_by('-id'))
        else:
            return Response({'detail': 'Permission denied: include Race-Api-Key or log in to ROBis with manager permission.'},
                            status=status.HTTP_403_FORBIDDEN)

        items = []
        for o in qs:
            r = o.race
            items.append({
                'id': o.id,
                'race_id': o.race_id,
                'race_name': r.race_name if r else None,
                'event_name': r.event.event_name if (r and r.event_id) else None,
                'competitor_index': o.competitor_index,
                'competitor_old_si_number': o.old_si_number,
                'competitor_new_si_number': o.new_si_number,
                'competitor_start_number': o.competitor_start_number,
                'competitor_name': o.competitor_full_name,
                'competitor_club': o.competitor_club,
                'competitor_category_name': o.competitor_category_name,
                'competitor_start_time': o.competitor_start_time.strftime('%Y-%m-%dT%H:%M:%S'),
                'comment': o.comment,
                'changed_time': o.time_changes,
                'recieved': o.timestamp,
            })

        return Response(items, status=status.HTTP_200_OK)



    def post(self, request):
        raw = request.body.decode('utf-8', errors='ignore')
        if not raw:
            return Response({'detail': 'Missing payload in body.'}, status=status.HTTP_400_BAD_REQUEST)

        # --- minimalist parser (inside post) ---
        def _yaml_fallback_parse(raw: str):
            def _val(s: str):
                s = s.strip()
                if s.lower() == 'null': return None
                return s.strip('"')

            out = {'Version': None, 'Creator': None, 'Event': None, 'Data': []}
            m = re.search(r'^\s*Version:\s*(.+)$', raw, re.MULTILINE)
            if m: out['Version'] = _val(m.group(1))
            m = re.search(r'^\s*Creator:\s*(.+)$', raw, re.MULTILINE)
            if m: out['Creator'] = _val(m.group(1))
            m = re.search(r'^\s*Event:\s*(.+)$', raw, re.MULTILINE)
            if m: out['Event'] = _val(m.group(1))

            data_sec = re.split(r'^\s*Data:\s*$', raw, flags=re.MULTILINE)
            if len(data_sec) < 2:
                return out

            data_body = data_sec[1]
            items = re.split(r'^\s*-\s*Runner:\s*$', data_body, flags=re.MULTILINE)
            for chunk in items[1:]:
                parts = re.split(r'^\s*ChangeLog:\s*$', chunk, flags=re.MULTILINE, maxsplit=1)
                runner_block = parts[0]
                changelog_block = parts[1] if len(parts) == 2 else ''

                def parse_block(block: str):
                    d = {}
                    for line in block.splitlines():
                        m = re.match(r'^\s*([A-Za-z0-9_]+):\s*(.*)$', line)
                        if not m:
                            continue
                        key, val = m.group(1), m.group(2)
                        d[key] = _val(val)
                    return d

                runner = parse_block(runner_block)
                changelog = parse_block(changelog_block)
                out['Data'].append({'Runner': runner, 'ChangeLog': changelog})
            return out
        # --- /parser ---

        def parse_iso(x):
            if not x: return None
            s = str(x).strip()
            try:
                return datetime.fromisoformat(s.replace('Z', '+00:00'))
            except Exception:
                return parse_datetime(s)

        # “wall-clock preserve” ONLY for start_time:
        def wallclock_to_utc_same_clock(x):
            """
            Input: ISO string (eg. '2025-09-27T10:05:00+02:00' OR '...Z' OR without TZ)
            Output: aware UTC datetime with *same time* (=> '2025-09-27T10:05:00Z')
            """
            dt = parse_iso(x)
            if dt is None:
                return None
            # delete tzinfo/offset)
            naive_wall = dt.replace(tzinfo=None)
            # = UTC, no time convert
            return naive_wall.replace(tzinfo=dt_timezone.utc)

        doc = _yaml_fallback_parse(raw)
        data = (doc or {}).get('Data')
        if not isinstance(data, list):
            return Response({'detail': 'Non valid structure: must be in Data section.'}, status=status.HTTP_400_BAD_REQUEST)

        # race key
        race_api_key = None
        for k, v in request.headers.items():
            if k.lower() in ('key', 'race-api-key'):
                race_api_key = (v or '').strip() or None
                break
        race = Race.objects.filter(race_api_key=race_api_key).first() if race_api_key else None

        to_create, errors, skipped = [], [], 0

        def to_int(x):
            if x in (None, ''): return None
            try: return int(str(x).strip())
            except: return None

        with transaction.atomic():
            for i, item in enumerate(data, start=1):
                runner = (item or {}).get('Runner') or {}
                changelog = (item or {}).get('ChangeLog') or {}

                try:
                    competitor_index         = (runner.get('Id') or '').strip()
                    new_si_number            = to_int(runner.get('NewCard'))
                    old_si_number            = to_int(runner.get('Card'))
                    start_number             = to_int(runner.get('Bib'))
                    full_name                = (runner.get('Name') or '')
                    club                     = (runner.get('Org') or '')
                    class_name               = (runner.get('ClassName') or '')
                    comment                  = (runner.get('Comment') or '')

                    # >>> ONLY start_time “wall-clock preserve” <<<
                    start_time = wallclock_to_utc_same_clock(runner.get('StartTime'))

                    # Other times as usual:
                    ch_new     = parse_iso(changelog.get('NewCard'))
                    ch_comm    = parse_iso(changelog.get('Comment'))
                    time_changes = ch_new or ch_comm
                    if time_changes is None:
                        # no time_changes → continue
                        raise ValueError("Missing ChangeLog time (NewCard/Comment).")

                    if new_si_number is None or old_si_number is None:
                        raise ValueError("Missing NewCard or Card number.")

                    # DEDUP due time_changes (a race/null)
                    dup_filter = {'time_changes': time_changes}
                    if race is not None:
                        dup_filter['race'] = race
                    else:
                        dup_filter['race__isnull'] = True
                    if OchecklistStore.objects.filter(**dup_filter).exists():
                        skipped += 1
                        continue

                    to_create.append(OchecklistStore(
                        race = race,
                        racecieved_api_key = race_api_key,
                        competitor_index = competitor_index[:7],
                        new_si_number = new_si_number,
                        old_si_number = old_si_number,
                        competitor_start_number = start_number,
                        competitor_full_name = full_name,
                        competitor_club = club,
                        competitor_category_name = class_name,
                        comment = comment,
                        competitor_start_time = start_time,  # save 10:05:00Z (same time, no UTC convert)
                        time_changes = time_changes,
                    ))
                except Exception as e:
                    errors.append({'row': i, 'error': str(e)})

            if not to_create and (errors or skipped):
                return Response({'status': 'error', 'saved': 0, 'skipped': skipped, 'errors': errors}, status=status.HTTP_200_OK)

            OchecklistStore.objects.bulk_create(to_create, batch_size=500)

        return Response({
            'status': 'ok',
            'saved': len(to_create),
            'skipped': skipped,
            'errors': errors,
        }, status=status.HTTP_201_CREATED)
