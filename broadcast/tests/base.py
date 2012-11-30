#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import logging
import random
import string

from django.core.management import call_command
from django.db import DEFAULT_DB_ALIAS
from django.test import TestCase

from rapidsms.tests.scripted import TestScript as LegacyTestScript
from rapidsms.tests.harness import MockBackend
from rapidsms.router import get_router
from rapidsms.models import Connection, Contact, Backend

from groups.models import Group


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
