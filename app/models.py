
from django.db import models
from django.utils.translation import gettext_lazy as _

class Account(models.model):

    email               = models.EmailField(max_length=60, unique=True)
    username            = None
    first_name          = models.CharField(max_length=30, blank=False)
    last_name           = models.CharField(max_length=30, blank=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return f"{self.last_name} {self.first_name}, {self.email}"
    

class Role(models.Model):

    account             = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='account_role')
    index               = models.CharField(max_length=7, null=True, blank=True)

    def __str__(self):
        return f"{self.account.last_name} {self.account.first_name}, {self.index}"



class Event(models.Model):
        
    event_name          = models.CharField(max_length=50, null=False, blank=False, db_index=True)
    event_date_start    = models.DateField(null=False, blank=False, db_index=True)
    event_date_end      = models.DateField(null=True, blank=True, db_index=True)

    def __str__(self):  
        return self.event_name


class Race(models.Model):

    event               = models.ForeignKey(Event, on_delete=models.CASCADE)
    race_name           = models.CharField(max_length=50, null=False, blank=False)
    race_date           = models.DateField(null=False, blank=False)

    def __str__(self):  
        return self.race_name
    

class OchecklistStore(models.Model):

    class StatusType(models.TextChoices):
        OK = 'OK', _('OK')
        LATE = 'LATE', _('Pozdní start')
        DNS = 'DNS', _('Nestartoval')

    race                        = models.ForeignKey(Race, on_delete=models.SET_NULL, blank=True, null=True)
    racecieved_api_key          = models.CharField(max_length=50, blank=True, null=True)

    competitor_index            = models.CharField(max_length=7, blank=True)
    new_si_number               = models.PositiveIntegerField(blank=True, null=True)
    old_si_number               = models.PositiveIntegerField(blank=True, null=True)
    competitor_status           = models.CharField(max_length=4, choices=StatusType.choices, blank=True, default="")
    competitor_start_number     = models.PositiveIntegerField(blank=True, null=True)
    competitor_full_name        = models.CharField(max_length=40, blank=True)
    competitor_club             = models.CharField(max_length=80, blank=True)
    competitor_start_time       = models.DateTimeField(blank=False, null=True)  
    competitor_category_name    = models.CharField(max_length=30, blank=True)
    comment                     = models.CharField(max_length=200, blank=True)
    time_changes                = models.DateTimeField(blank=False, null=True)
    timestamp                   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.race.race_name} - {self.competitor_full_name} {self.competitor_category_name} - { self.comment}"
    

    





