#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import datetime
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.timezone import now as get_now

from rapidsms.apps.base import AppBase
from rapidsms.messages import OutgoingMessage
from rapidsms.router import send

from broadcast.models import Broadcast, BroadcastMessage, ForwardingRule
from broadcast.views import usage_report_context
from groups import models as groups

# In RapidSMS, message translation is done in OutgoingMessage, so no need
# to attempt the real translation here.  Use _ so that ./manage.py makemessages
# finds our text.
_ = lambda s: s


logger = logging.getLogger('broadcast.app')


def scheduler_callback():
    """ Prepare and send broadcast messages. """
    logger.info('Starting cron job.')
    queue_outgoing_messages()
    send_queued_messages()


def queue_outgoing_messages():
    """ Generate queued messages for scheduled broadcasts. """
    broadcasts = Broadcast.ready.all()
    logger.info('Found {0} ready broadcast(s)'.format(broadcasts.count()))
    for broadcast in broadcasts:
        # TODO: make sure this process is atomic
        count = broadcast.queue_outgoing_messages()
        logger.debug('Queued {0} broadcast message(s)'.format(count))
        broadcast.set_next_date()
        broadcast.save()


def send_queued_messages():
    """ Send messages which have been queued for delivery. """
    messages = BroadcastMessage.objects.filter(status='queued')[:50]
    logger.info('Found {0} message(s) to send'.format(messages.count()))
    for message in messages:
        connection = message.recipient.default_connection
        try:
            msg = send(message.broadcast.body, connection)[0]
        except Exception, e:
            msg = None
            logger.exception(e)
        if msg:
            logger.debug('Message sent successfully!')
            message.status = 'sent'
            message.date_sent = get_now()
        else:
            logger.debug('Message failed to send.')
            message.status = 'error'
        message.save()


def usage_email_callback(router, *args, **kwargs):
    """ Send out month email report of broadcast usage. """
    today = datetime.date.today()
    report_date = today - datetime.timedelta(days=today.day)
    start_date = datetime.date(report_date.year, report_date.month, 1)
    end_date = report_date
    context = usage_report_context(start_date, end_date)
    context['report_month'] = report_date.strftime('%B')
    context['report_year'] = report_date.strftime('%Y')
    subject_template = _(u'TrialConnect Monthly Report - {report_month} {report_year}')
    subject = subject_template.format(**context)
    body = render_to_string('broadcast/emails/usage_report_message.html', context)
    group_name = settings.DEFAULT_MONTHLY_REPORT_GROUP_NAME
    group, created = groups.Group.objects.get_or_create(name=group_name)
    if not created:
        emails = [c.email for c in group.contacts.all() if c.email]
        send_mail(subject, body, None, emails, fail_silently=True)


class BroadcastApp(AppBase):
    """ RapidSMS app to send broadcast messages """

    not_registered = _('Sorry, your mobile number is not registered in the '
                       'required group for this keyword.')
    thank_you = _('Thank you, your message has been queued for delivery.')

    def start(self):
        self.info('started')

    def _forwarding_rules(self):
        """ Returns a dictionary mapping rule keywords to rule objects """
        rules = ForwardingRule.objects.all()
        return dict([(rule.keyword.lower(), rule) for rule in rules])

    def handle(self, msg):
        """
        Handles messages that match the forwarding rules in this app.
        """
        msg_parts = msg.text.split()
        rules = self._forwarding_rules()
        if not msg_parts:
            return False
        keyword = msg_parts[0].lower()
        if keyword not in rules:
            self.debug(u'{0} keyword not found in rules'.format(keyword))
            return False
        rule = rules[keyword]
        contact = msg.connection.contact
        if not contact or \
          not rule.source.contacts.filter(pk=contact.pk).exists():
            msg.respond(self.not_registered)
            return True
        now = get_now()
        msg_text = [rule.message, u' '.join(msg_parts[1:])]
        msg_text = [m for m in msg_text if m]
        msg_text = u' '.join(msg_text)
        full_msg = u'From {name} ({number}): {body}'\
                   .format(name=contact.name, number=msg.connection.identity,
                           body=msg_text)
        broadcast = Broadcast.objects.create(date_created=now, date=now,
                                             schedule_frequency='one-time',
                                             body=full_msg, forward=rule)
        broadcast.groups.add(rule.dest)
        msg.respond(self.thank_you)
