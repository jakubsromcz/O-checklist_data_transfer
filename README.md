# O-checklist -> rob-is.cz -> your readout app
### Easy transfer of changed competitors data (si number, start time etc.) from O-checklist to your readout app in the finish.
1) Connect **O-checklist** app with **[rob-is.cz](https://rob-is.cz/)** with **POST** requests. [How to do it?](https://rob-is.cz/napoveda#other-ochecklist).
2) Pull this data from **rob-is.cz** with **GET** request [from endpoint](https://rob-is.cz/napoveda#dev-api).

- Easy to use 
- Available 24/7
- No registration needed

### Endpoint:

```
https://rob-is.cz/api/ochecklist/
```
### GET example:
```
[
  {
      "id": 1,
      "race_id": 520,
      "race_name": "MČR 144 MHz",
      "event_name": "Bílovické krpály 2025",
      "competitor_status": "DNS",
      "competitor_index": "GAP7755",
      "competitor_old_si_number": 1775519,
      "competitor_new_si_number": 6658,
      "competitor_start_number": null,
      "competitor_name": "Hana Fučíková",
      "competitor_club": "O-sport z.s.",
      "competitor_category_name": "D35",
      "competitor_start_time": "2025-09-27T10:05:00",
      "comment": "late start, si num changed",
      "changed_time": "2025-10-27T17:18:06Z",
      "recieved": "2025-10-28T08:24:47.290665Z"
  }
]
```
### Note: offering this software as a managed service is not permitted