import datetime

from django import forms
from django.forms.models import modelformset_factory
from django.utils.dates import MONTHS

from aremind.apps.broadcast.models import Broadcast, ForwardingRule
from aremind.apps.broadcast.validators import validate_keyword
from aremind.apps.groups.models import Group


class BroadcastForm(forms.ModelForm):
    """ Form to send a broadcast message """

    SEND_CHOICES = (
        ('now', 'Now'),
        ('later', 'Later'),
    )
    when = forms.ChoiceField(label='Send', choices=SEND_CHOICES)
    body = forms.CharField(label="Message", max_length=140,
                           widget=forms.Textarea)

    class Meta(object):
        model = Broadcast
        exclude = ('date_created', 'date_last_notified', 'date_next_notified')

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        if instance and instance.pk:
            kwargs['initial'] = {'when': 'later'}
        super(BroadcastForm, self).__init__(*args, **kwargs)
        if instance and instance.pk:
            self.fields['when'].widget = forms.HiddenInput()
        picker_class = 'datetimepicker'
        self.fields['date'].label = 'Start date'
        self.fields['date'].required = False
        self.fields['date'].widget.attrs['class'] = picker_class
        self.fields['schedule_end_date'].widget.attrs['class'] = picker_class
        widget_class = 'multiselect'
        self.fields['weekdays'].help_text = ''
        self.fields['weekdays'].widget.attrs['class'] = widget_class
        self.fields['months'].help_text = ''
        self.fields['months'].widget.attrs['class'] = widget_class
        self.fields['groups'].help_text = ''
        self.fields['groups'].widget.attrs['class'] = widget_class
        self.fields['body'].widget.attrs['class'] = 'test-messager-field'
        # hide disabled frequency in form
        choices = list(Broadcast.REPEAT_CHOICES)
        choices.pop(0)
        self.fields['schedule_frequency'].choices = choices
        self.fields.keyOrder = ('when', 'date', 'schedule_frequency', 
                                'schedule_end_date','weekdays', 'months',
                                'body', 'groups')

    def clean(self):
        when = self.cleaned_data['when']
        date = self.cleaned_data['date']
        if when == 'later' and not date:
            raise forms.ValidationError('Start date is required for future broadcasts')
        end_date = self.cleaned_data['schedule_end_date']
        if end_date and end_date < date:
            raise forms.ValidationError('End date must be later than start date')
        return self.cleaned_data

    def save(self, commit=True):
        broadcast = super(BroadcastForm, self).save(commit=False)
        if self.cleaned_data['when'] == 'now':
            broadcast.date = datetime.datetime.now()
        if commit:
            broadcast.save()
            # pylint: disable=E1101
            self.save_m2m()
            frequency = self.cleaned_data['schedule_frequency']
            if frequency != 'weekly':
                broadcast.weekdays = []
            if frequency != 'monthly':
                broadcast.months = []
        return broadcast


ForwardingRuleFormset = modelformset_factory(ForwardingRule, can_delete=True)


class ForwardingRuleForm(forms.ModelForm):

    class Meta(object):
        model = ForwardingRule

    def __init__(self, *args, **kwargs):
        super(ForwardingRuleForm, self).__init__(*args, **kwargs)
        if validate_keyword not in self.fields['keyword'].validators:
            self.fields['keyword'].validators.append(validate_keyword)
        self.fields['keyword'].help_text = validate_keyword.help_text


class ReportForm(forms.Form):
    report_month = forms.TypedChoiceField(label='Report Month', required=False,
        coerce=int, choices=MONTHS.items(), 
    )
    report_year = forms.IntegerField(label='Report Year', required=False,
        min_value=1970, max_value=datetime.date.today().year
    )


class RecentMessageForm(forms.Form):
    groups = forms.ModelMultipleChoiceField(queryset=Group.objects.all())

