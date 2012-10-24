# vim: ai ts=4 sts=4 et sw=4
import logging
import datetime
from dateutil.relativedelta import relativedelta
from dateutil import rrule

from django.db import models

from rapidsms.models import Contact, Connection
from rapidsms.contrib.messagelog.models import Message

from aremind.apps.groups.models import Group


logger = logging.getLogger('broadcast.models')


class DateAttribute(models.Model):
    """ Simple model to store weekdays and months """

    ATTRIBUTE_TYPES = (
        ('weekday', 'Weekday'),
        ('month', 'Month'),
    )
    WEEKDAY_CHOICES = (
        (0, 'Sunday'),
        (1, 'Monday'),
        (2, 'Tuesday'),
        (3, 'Wednesday'),
        (4, 'Thursday'),
        (5, 'Friday'),
        (6, 'Saturday'),
    )
    MONTH_CHOICES = (
        (0, 'January'),
        (1, 'February'),
        (2, 'March'),
        (3, 'April'),
        (4, 'May'),
        (5, 'June'),
        (6, 'July'),
        (7, 'August'),
        (8, 'September'),
        (9, 'October'),
        (10, 'November'),
        (11, 'December'),
    )

    name = models.CharField(max_length=32, unique=True)
    value = models.PositiveSmallIntegerField()
    type = models.CharField(max_length=16, choices=ATTRIBUTE_TYPES)

    class Meta(object):
        unique_together = ('type', 'value')
        ordering = ('value',)

    def __unicode__(self):
        return self.name


class BroadcastReadyManager(models.Manager):
    def get_query_set(self):
        qs = super(BroadcastReadyManager, self).get_query_set()
        qs = qs.filter(date__lt=datetime.datetime.now())
        qs = qs.exclude(schedule_frequency__isnull=True)
        return qs


class Broadcast(models.Model):
    """ General broadcast message """

    REPEAT_CHOICES = (
        (None, 'Disabled'),
        ('one-time', 'One Time'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    )

    date_created = models.DateTimeField()
    date_last_notified = models.DateTimeField(null=True, blank=True)
    date = models.DateTimeField(db_index=True)
    schedule_end_date = models.DateTimeField(null=True, blank=True)
    schedule_frequency = models.CharField(max_length=16, blank=True, null=True,
                                          choices=REPEAT_CHOICES,
                                          db_index=True)
    weekdays = models.ManyToManyField(DateAttribute, blank=True,
                                      limit_choices_to={'type': 'weekday'},
                                      related_name='broadcast_weekdays')
    months = models.ManyToManyField(DateAttribute, blank=True,
                                    limit_choices_to={'type': 'month'},
                                    related_name='broadcast_months')
    body = models.TextField()
    groups = models.ManyToManyField(Group, related_name='broadcasts')
    forward = models.ForeignKey('ForwardingRule', related_name='broadcasts',
                                null=True, blank=True)

    objects = models.Manager()
    ready = BroadcastReadyManager()

    def __unicode__(self):
        if self.schedule_frequency:
            freq = self.schedule_frequency
        else:
            freq = 'disabled'
        if self.date:
            date = self.date.isoformat(' ')
        else:
            date = 'None'
        return '{0} broadcast (date {1})'.format(freq, date)

    def get_next_date(self):
        """ calculate next date based on configured characteristics """
        logger.debug('get_next_date - {0}'.format(self))
        now = datetime.datetime.now()
        # return current date if it's in the future
        if self.date > now:
            return self.date
        # no next date if broadcast is disabled or one-time
        one_time = self.schedule_frequency == 'one-time'
        # no next date if end date has passed
        end_date_reached = False
        if self.schedule_end_date:
            end_date_reached = self.schedule_end_date < now
        if not self.schedule_frequency or one_time or end_date_reached:
            return None
        freq_map = {
            'daily': rrule.DAILY,
            'weekly': rrule.WEEKLY,
            'monthly': rrule.MONTHLY,
            'yearly': rrule.YEARLY,
        }
        freq = freq_map.get(self.schedule_frequency)
        kwargs = {'dtstart': self.date}
        if freq == rrule.WEEKLY:
            weekdays = self.weekdays.values_list('value', flat=True)
            if weekdays:
                kwargs['byweekday'] = weekdays
        elif freq == rrule.MONTHLY:
            months = self.months.values_list('value', flat=True)
            if months:
                kwargs['bymonth'] = months
        dates = rrule.rrule(freq, **kwargs)
        for date in dates:
            logger.debug('looking for next date {0}'.format(date))
            if date > now:
                logger.debug('next date {0}'.format(date))
                return date

    def set_next_date(self):
        """ update broadcast to be ready for next date """
        logger.debug('set_next_date start - {0}'.format(self))
        now = datetime.datetime.now()
        next_date = self.get_next_date()
        # Disable this broadcast if it was a one-time notification (we just
        # sent it). This will make get_next_date() return None below.
        if self.schedule_frequency == 'one-time':
            self.schedule_frequency = None
        self.date_last_notified = now
        if next_date:
            self.date = next_date
        logger.debug('set_next_date end - {0}'.format(self))

    def queue_outgoing_messages(self):
        """ generate queued outgoing messages """
        contacts = Contact.objects.distinct().filter(groups__broadcasts=self)
        for contact in contacts:
            self.messages.create(recipient=contact)
        return contacts.count()

    def save(self, **kwargs):
        if not self.pk:
            self.date_created = datetime.datetime.now()
        return super(Broadcast, self).save(**kwargs)


class BroadcastMessage(models.Model):
    """ Message to individual recipient of broadcast """

    STATUS_CHOICES = (
        ('queued', 'Queued'),
        ('sent', 'Sent'),
        ('error', 'Error'),
    )

    broadcast = models.ForeignKey(Broadcast, related_name='messages')
    recipient = models.ForeignKey(Contact, related_name='broadcast_messages')
    date_created = models.DateTimeField()
    date_sent = models.DateTimeField(null=True, blank=True, db_index=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES,
                              default='queued', db_index=True)

    def save(self, **kwargs):
        if not self.pk:
            self.date_created = datetime.datetime.now()
        return super(BroadcastMessage, self).save(**kwargs)


class ForwardingRule(models.Model):
    """ Rule for forwarding SMSes from a user in one group to a 2nd group """

    keyword = models.CharField(max_length=160, unique=True)
    source = models.ForeignKey(Group, related_name='source_rules')
    dest = models.ForeignKey(Group, related_name='dest_rules')
    message = models.CharField(max_length=160, blank=True)
    rule_type = models.CharField(verbose_name='type', max_length=100,
        blank=True, null=True,
        help_text="""Types organize forwarding rules by their purpose.
            For instance there might be multiple keywords that trigger the same actions.
            Examples would be 'Cold Chain' or 'Staff Communication'."""
    )
    label = models.CharField(max_length=150, blank=True, null=True,
        help_text="""Labels organize forwarding rules within their type. 
            For instance you might give rules with the same source or destination a common label.
            Examples would be 'System Messages' or 'To Staff'."""
    )

    def __unicode__(self):
        return self.keyword
