from django.core.exceptions import ValidationError

from aremind.apps.reminders.app import RemindersApp


def validate_keyword(value):
    if value == RemindersApp.conf_keyword:
        msg = u"'%s' is a keyword reserved for the appointment reminders." %  RemindersApp.conf_keyword
        raise ValidationError(msg)
    if RemindersApp.pin_regex.match(value):
        msg = u"This keyword matches the appointment reminder PIN regex: %s" %  RemindersApp.pin_regex.pattern
        raise ValidationError(msg)
validate_keyword.help_text = u"""
Messages will be forwarded based on matching the start of the message to the given keyword.
There are a few keywords which you must avoid because of conflicts with other applications:
'%(conf)s' and keywords matching the regular expression '%(pattern)s' are currently
used by the appointment reminders application.""" % {
    'conf': RemindersApp.conf_keyword,
    'pattern': RemindersApp.pin_regex.pattern,
}
