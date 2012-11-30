#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import datetime
from dateutil import rrule
from dateutil.relativedelta import relativedelta

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from rapidsms.messages.incoming import IncomingMessage
from rapidsms.router import get_router
from rapidsms.tests.harness import MockRouter, MockBackend

from broadcast.app import BroadcastApp, scheduler_callback
from broadcast.forms import BroadcastForm
from broadcast.models import Broadcast, ForwardingRule
from broadcast.tests.base import BroadcastCreateDataTest


class DateAttributeTest(BroadcastCreateDataTest):
    """ Test pre-defined data in initial_data.json against rrule constants """

    def test_weekdays(self):
        """ Test weekdays match """
        self.assertEqual(self.get_weekday('monday').value, rrule.MO.weekday)
        self.assertEqual(self.get_weekday('tuesday').value, rrule.TU.weekday)
        self.assertEqual(self.get_weekday('wednesday').value, rrule.WE.weekday)
        self.assertEqual(self.get_weekday('thursday').value, rrule.TH.weekday)
        self.assertEqual(self.get_weekday('friday').value, rrule.FR.weekday)
        self.assertEqual(self.get_weekday('saturday').value, rrule.SA.weekday)
        self.assertEqual(self.get_weekday('sunday').value, rrule.SU.weekday)


class BroadcastDateTest(BroadcastCreateDataTest):

    def test_get_next_date_future(self):
        """ get_next_date shouldn't increment if date is in the future """
        date = datetime.datetime.now() + relativedelta(hours=1)
        broadcast = self.create_broadcast(date=date)
        self.assertEqual(broadcast.get_next_date(), date)
        broadcast.set_next_date()
        self.assertEqual(broadcast.date, date,
                         "set_next_date should do nothing")

    def test_get_next_date_past(self):
        """ get_next_date should increment if date is in the past """
        date = datetime.datetime.now() - relativedelta(hours=1)
        broadcast = self.create_broadcast(date=date)
        self.assertTrue(broadcast.get_next_date() > date)
        broadcast.set_next_date()
        self.assertTrue(broadcast.date > date,
                        "set_next_date should increment date")

    def test_one_time_broadcast(self):
        """ one-time broadcasts should disable and not increment """
        date = datetime.datetime.now()
        broadcast = self.create_broadcast(date=date,
                                          schedule_frequency='one-time')
        self.assertEqual(broadcast.get_next_date(), None,
                         "one-time broadcasts have no next date")
        broadcast.set_next_date()
        self.assertEqual(broadcast.date, date,
                         "set_next_date shoudn't change date of one-time")
        self.assertEqual(broadcast.schedule_frequency, None,
                         "set_next_date should disable one-time")

    def test_by_weekday_yesterday(self):
        """ Test weekday recurrences for past day """
        yesterday = datetime.datetime.now() - relativedelta(days=1)
        data = {'date': yesterday, 'schedule_frequency': 'weekly',
                'weekdays': [self.get_weekday_for_date(yesterday)]}
        broadcast = self.create_broadcast(**data)
        next = yesterday + relativedelta(weeks=1)
        self.assertDateEqual(broadcast.get_next_date(), next)

    def test_by_weekday_tomorrow(self):
        """ Test weekday recurrences for future day (shouldn't change) """
        tomorrow = datetime.datetime.now() + relativedelta(days=1)
        data = {'date': tomorrow, 'schedule_frequency': 'weekly',
                'weekdays': [self.get_weekday_for_date(tomorrow)]}
        broadcast = self.create_broadcast(**data)
        self.assertDateEqual(broadcast.get_next_date(), tomorrow)

    def test_end_date_disable(self):
        """ Broadcast should disable once end date is reached """
        broadcast = self.create_broadcast(when='ready')
        broadcast.schedule_end_date = datetime.datetime.now()
        self.assertEqual(broadcast.get_next_date(), None)

    def test_month_recurrence(self):
        """ Test monthly recurrence for past month """
        day = datetime.datetime.now() + relativedelta(days=1)
        one_month_ago = day - relativedelta(months=1)
        broadcast = self.create_broadcast(date=one_month_ago,
                                          schedule_frequency='monthly')
        self.assertDateEqual(broadcast.get_next_date(), day)

    def test_bymonth_recurrence(self):
        """ Test bymonth recurrence for past month """
        day = datetime.datetime.now() + relativedelta(days=1)
        one_month_ago = day - relativedelta(months=1)
        next_month = day + relativedelta(months=1)
        months = (self.get_month_for_date(one_month_ago),
                  self.get_month_for_date(next_month))
        data = {'date': one_month_ago, 'schedule_frequency': 'monthly',
                'months': months}
        broadcast = self.create_broadcast(**data)
        self.assertDateEqual(broadcast.get_next_date(), next_month)


class BroadcastAppTest(BroadcastCreateDataTest):

    def test_queue_creation(self):
        """ Test broadcast messages are queued properly """
        c1 = self.create_contact()
        g1 = self.create_group()
        c1.groups.add(g1)
        c2 = self.create_contact()
        g2 = self.create_group()
        c2.groups.add(g2)
        broadcast = self.create_broadcast(groups=[g1])
        broadcast.queue_outgoing_messages()
        self.assertEqual(broadcast.messages.count(), 1)
        contacts = broadcast.messages.values_list('recipient', flat=True)
        self.assertTrue(c1.pk in contacts)
        self.assertFalse(c2.pk in contacts)

    def test_ready_manager(self):
        """ test Broadcast.ready manager returns broadcasts ready to go out """
        b1 = self.create_broadcast(when='ready')
        b2 = self.create_broadcast(when='future')
        ready = Broadcast.ready.values_list('id', flat=True)
        self.assertTrue(b1.pk in ready)
        self.assertFalse(b2.pk in ready)


class BroadcastFormTest(BroadcastCreateDataTest):
    def setUp(self):
        self.contact = self.create_contact()
        self.group = self.create_group()
        self.contact.groups.add(self.group)

    def test_future_start_date_required(self):
        """ Start date is required for future broadcasts """
        data =  {
            'when': 'later',
            'body': self.random_string(140),
            'schedule_frequency': 'one-time',
            'groups': [self.group.pk],
        }
        form = BroadcastForm(data)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)
        msg = 'Start date is required for future broadcasts'
        self.assertTrue(msg in form.non_field_errors().as_text())

    def test_now_date_set_on_save(self):
        """ 'now' messages automatically get date assignment """
        data =  {
            'when': 'now',
            'body': self.random_string(140),
            'groups': [self.group.pk],
        }
        form = BroadcastForm(data)
        self.assertTrue(form.is_valid())
        broadcast = form.save()
        self.assertTrue(broadcast.date is not None)

    def test_end_date_before_start_date(self):
        """ Form should prevent end date being before start date """
        now = datetime.datetime.now()
        yesterday = now - relativedelta(days=1)
        data =  {
            'when': 'later',
            'body': self.random_string(140),
            'date': now,
            'schedule_end_date': yesterday,
            'schedule_frequency': 'daily',
            'groups': [self.group.pk],
        }
        form = BroadcastForm(data)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)
        msg = 'End date must be later than start date'
        self.assertTrue(msg in form.non_field_errors().as_text())

    def test_update(self):
        """ Test broadcast edit functionality """
        before = self.create_broadcast(when='future', groups=[self.group.pk])
        data =  {
            'when': 'later',
            'date': before.date,
            'body': self.random_string(30),
            'schedule_frequency': before.schedule_frequency,
            'groups': [self.group.pk],
        }
        form = BroadcastForm(data, instance=before)
        self.assertTrue(form.is_valid(), form._errors.as_text())
        before = Broadcast.objects.get(pk=before.pk)
        after = form.save()
        # same broadcast
        self.assertEqual(before.pk, after.pk)
        # new message
        self.assertNotEqual(before.body, after.body)

    def test_field_clearing(self):
        """ Non related frequency fields should be cleared on form clean """
        weekday = self.get_weekday_for_date(datetime.datetime.now())
        before = self.create_broadcast(when='future', groups=[self.group.pk],
                                       weekdays=[weekday])
        data =  {
            'when': 'later',
            'date': before.date,
            'body': before.body,
            'schedule_frequency': 'monthly',
            'groups': [self.group.pk],
            'weekdays': [weekday.pk],
        }
        form = BroadcastForm(data, instance=before)
        after = form.save()
        self.assertEqual(after.weekdays.count(), 0)


class BroadcastViewTest(BroadcastCreateDataTest):
    def setUp(self):
        self.user = User.objects.create_user('test', 'a@b.com', 'abc')
        self.user.save()
        self.client.login(username='test', password='abc')

    def test_delete(self):
        """ Make sure broadcasts are disabled on 'delete' """
        contact = self.create_contact()
        group = self.create_group()
        contact.groups.add(group)
        before = self.create_broadcast(when='future', groups=[group.pk])
        url = reverse('delete-broadcast', args=[before.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302,
                         'should redirect on success')
        after = Broadcast.objects.get(pk=before.pk)
        self.assertTrue(after.schedule_frequency is None)


class BroadcastForwardingTest(BroadcastCreateDataTest):

    def setUp(self):
        self.source_contact = self.create_contact()
        self.dest_contact = self.create_contact()
        self.backend = self.create_backend(name='mockbackend')
        self.unreg_conn = self.create_connection(backend=self.backend)
        self.source_conn = self.create_connection(contact=self.source_contact,
                                                  backend=self.backend,
                                                  identity='5678')
        self.dest_conn = self.create_connection(contact=self.dest_contact,
                                                backend=self.backend,
                                                identity='1234')
        self.router = MockRouter()
        self.app = BroadcastApp(router=self.router)
        self.rule = self.create_forwarding_rule(keyword='abc')
        self.rule.source.contacts.add(self.source_contact)

    def _send(self, conn, text):
        msg = IncomingMessage(conn, text)
        self.app.handle(msg)
        return msg

    def test_non_matching_rule(self):
        """ tests that no response comes for non-matching keywords """
        msg = self._send(self.source_conn, 'non-matching-keyword')
        self.assertEqual(len(msg.responses), 0)

    def test_unregistered(self):
        """ tests the response from an unregistered user """
        msg = self._send(self.unreg_conn, 'abc')
        self.assertEqual(len(msg.responses), 1)
        self.assertEqual(msg.responses[0].text,
                         self.app.not_registered)

    def test_wrong_group(self):
        """ tests the response from a user in non-source group """
        msg = self._send(self.dest_conn, 'abc')
        self.assertEqual(len(msg.responses), 1)
        self.assertEqual(msg.responses[0].text,
                         self.app.not_registered)

    def test_creates_broadcast(self):
        """ tests the response from a user in non-source group """
        msg = self._send(self.source_conn, 'abc my-message')
        now = datetime.datetime.now()
        self.assertEqual(len(msg.responses), 1)
        self.assertEqual(Broadcast.objects.count(), 1)
        bc = Broadcast.objects.get()
        self.assertDateEqual(bc.date_created, now)
        self.assertDateEqual(bc.date, now)
        self.assertEqual(bc.schedule_frequency, 'one-time')
        expected_msg = 'From {name} ({number}): {msg} my-message'\
                       .format(name=self.source_contact.name,
                               number=self.source_conn.identity,
                               msg=self.rule.message)
        self.assertEqual(bc.body, expected_msg)
        self.assertEqual(list(bc.groups.all()), [self.rule.dest])
        self.assertEqual(msg.responses[0].text,
                         self.app.thank_you)

    def test_unicode_broadcast_body(self):
        """ Make sure unicode strings can be broadcasted """
        text = u'abc ' + self.random_unicode_string(2)
        msg = self._send(self.source_conn, text)
        self.assertEqual(len(msg.responses), 1)
        self.assertEqual(Broadcast.objects.count(), 1)

    def test_rule_tracking(self):
        """Test the broadcast is correctly associated with the rule via FK."""
        msg = self._send(self.source_conn, 'abc my-message')
        self.assertEqual(Broadcast.objects.count(), 1)
        bc = Broadcast.objects.get()
        self.assertEqual(bc.forward, self.rule)


class BroadcastScriptedTest(BroadcastCreateDataTest):

    def setUp(self):
        super(BroadcastScriptedTest, self).setUp()
        backends = {'mockbackend': {'ENGINE': MockBackend}}
        self.router = get_router()(backends=backends)

    def test_entire_stack(self):
        contact = self.create_contact()
        backend = self.create_backend(name='mockbackend')
        connection = self.create_connection(contact=contact, backend=backend)
        # ready broadcast
        g1 = self.create_group()
        contact.groups.add(g1)
        b1 = self.create_broadcast(when='ready', groups=[g1])
        # non-ready broadcast
        g2 = self.create_group()
        contact.groups.add(g2)
        b2 = self.create_broadcast(when='future', groups=[g2])
        # run cronjob
        scheduler_callback()
        # one sent message (future broadcast isn't ready)
        self.assertEquals(contact.broadcast_messages.count(), 1)
        message = contact.broadcast_messages.get()
        self.assertEquals(message.status, 'sent')
        self.assertTrue(message.date_sent is not None)


class ForwardingViewsTest(BroadcastCreateDataTest):

    def setUp(self):
        super(ForwardingViewsTest, self).setUp()
        self.user = User.objects.create_user('test', 'a@b.com', 'abc')
        self.user.save()
        self.client.login(username='test', password='abc')
        self.dashboard_url = reverse('broadcast-forwarding')

    def get_valid_data(self):
        data = {
            'keyword': self.random_string(length=25),
            'source': self.create_group(name=self.random_string(length=25)).pk,
            'dest': self.create_group(name=self.random_string(length=25)).pk,
            'message': self.random_string(length=25),
        }
        return data

    def test_forwarding_dashboard(self):
        """
        Test that the forwarding rule dashboard loads properly.
        """

        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)

    def test_get_create_page(self):
        """
        Test retriving the create forwarding rule form.
        """

        url = reverse('broadcast-forwarding-create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_notification(self):
        """
        Test creating forwarding rule via form.
        """

        start_count = ForwardingRule.objects.count()
        url = reverse('broadcast-forwarding-create')
        data = self.get_valid_data()
        response = self.client.post(url, data)
        self.assertRedirects(response, self.dashboard_url)
        end_count = ForwardingRule.objects.count()
        self.assertEqual(end_count, start_count + 1)

    def test_get_edit_page(self):
        """
        Test retriving the edit forwarding rule form.
        """

        data = self.get_valid_data()
        rule = self.create_forwarding_rule()
        url = reverse('broadcast-forwarding-edit', args=[rule.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_edit_notification(self):
        """
        Test editing forwarding rule via form.
        """

        data = self.get_valid_data()
        rule = self.create_forwarding_rule()
        start_count = ForwardingRule.objects.count()
        url = reverse('broadcast-forwarding-edit', args=[rule.pk])
        response = self.client.post(url, data)
        self.assertRedirects(response, self.dashboard_url)
        end_count = ForwardingRule.objects.count()
        self.assertEqual(end_count, start_count)

    def test_get_delete_page(self):
        """
        Test retriving the delete forwarding rule form.
        """

        rule = self.create_forwarding_rule()
        url = reverse('broadcast-forwarding-delete', args=[rule.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_delete_notification(self):
        """
        Test delete forwarding rule via form.
        """

        rule = self.create_forwarding_rule()
        start_count = ForwardingRule.objects.count()
        url = reverse('broadcast-forwarding-delete', args=[rule.pk])
        response = self.client.post(url, {})
        self.assertRedirects(response, self.dashboard_url)
        end_count = ForwardingRule.objects.count()
        self.assertEqual(end_count, start_count - 1)

