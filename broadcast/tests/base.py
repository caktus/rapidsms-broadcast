#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import datetime
from dateutil.relativedelta import relativedelta
import logging
import random
import string

from django.core.management import call_command
from django.db import DEFAULT_DB_ALIAS
from django.test import TestCase

from rapidsms.models import Connection, Contact, Backend
from rapidsms.router import get_router
from rapidsms.tests.harness import MockBackend

from groups.models import Group

from broadcast.models import ForwardingRule, DateAttribute, Broadcast


UNICODE_CHARS = [unichr(x) for x in xrange(1, 0xD7FF)]


class CreateDataTest(TestCase):
    """ Base test case that provides helper functions to create data """

    def random_string(self, length=255, extra_chars=''):
        chars = string.letters + extra_chars
        return ''.join([random.choice(chars) for i in range(length)])

    def random_number_string(self, length=4):
        numbers = [str(x) for x in random.sample(range(10), 4)]
        return ''.join(numbers)

    def random_unicode_string(self, max_length=255):
        output = u''
        for x in xrange(random.randint(1, max_length/2)):
            c = UNICODE_CHARS[random.randint(0, len(UNICODE_CHARS)-1)]
            output += c + u' '
        return output

    def create_backend(self, **kwargs):
        defaults = {
            'name': self.random_string(12),
        }
        defaults.update(kwargs)
        return Backend.objects.create(**defaults)

    def create_contact(self, **kwargs):
        defaults = {
            'name': self.random_string(12),
        }
        defaults.update(kwargs)
        return Contact.objects.create(**defaults)

    def create_connection(self, **kwargs):
        defaults = {
            'identity': self.random_string(10),
        }
        defaults.update(kwargs)
        if 'backend' not in defaults:
            defaults['backend'] = self.create_backend()
        return Connection.objects.create(**defaults)

    def create_group(self, **kwargs):
        defaults = {
            'name': self.random_string(12),
        }
        defaults.update(kwargs)
        return Group.objects.create(**defaults)


class BroadcastCreateDataTest(CreateDataTest):
    """ Base test case that provides helper functions for Broadcast data """

    def create_broadcast(self, when='', groups=None, weekdays=None,
            months=None, **kwargs):
        date = datetime.datetime.now()
        if when == 'ready':  # broadcast is in the past
            date -= relativedelta(days=1)
        elif when == 'future':  # broadcast is in the future
            date += relativedelta(days=1)
        defaults = {
            'date': date,
            'schedule_frequency': 'daily',
            'body': self.random_string(140),
        }
        defaults.update(kwargs)
        broadcast = Broadcast.objects.create(**defaults)
        if groups:
            broadcast.groups = groups
        if weekdays:
            broadcast.weekdays = weekdays
        if months:
            broadcast.months = months
        return broadcast

    def create_forwarding_rule(self, **kwargs):
        defaults = {
            'keyword': self.random_string(length=25),
            'source': self.create_group(name=self.random_string(length=25)),
            'dest': self.create_group(name=self.random_string(length=25)),
            'message': self.random_string(length=25),
        }
        defaults.update(kwargs)
        return ForwardingRule.objects.create(**defaults)

    def get_weekday(self, day):
        return DateAttribute.objects.get(name__iexact=day,
                                         type__exact='weekday')

    def get_weekday_for_date(self, date):
        return DateAttribute.objects.get(value=date.weekday(),
                                         type__exact='weekday')

    def get_month(self, day):
        return DateAttribute.objects.get(name__iexact=day, type__exact='month')

    def get_month_for_date(self, date):
        return DateAttribute.objects.get(value=date.month, type__exact='month')

    def assertDateEqual(self, date1, date2):
        """ date comparison that ignores microseconds """
        date1 = date1.replace(microsecond=0)
        date2 = date2.replace(microsecond=0)
        self.assertEqual(date1, date2)
