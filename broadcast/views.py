import calendar
import datetime

from django.db import transaction
from django.core.urlresolvers import reverse
from django.conf import settings
from django.template.context import RequestContext
from django.shortcuts import render_to_response, redirect
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import simplejson as json

from rapidsms.contrib.messagelog.models import Message

from aremind.apps.broadcast.forms import BroadcastForm, ForwardingRuleForm, ReportForm, RecentMessageForm
from aremind.apps.broadcast.models import Broadcast, BroadcastMessage, ForwardingRule
from aremind.apps.patients.models import Patient
from aremind.apps.reminders.models import SentNotification
from aremind.apps.wisepill.constants import WISEPILL_LOW_BATTERY


@login_required
@transaction.commit_on_success
def send_message(request, broadcast_id=None):
    if broadcast_id:
        broadcast = get_object_or_404(Broadcast, pk=broadcast_id)
    else:
        broadcast = None
    if request.method == 'POST':
        form = BroadcastForm(request.POST, instance=broadcast)
        if form.is_valid():
            broadcast = form.save()
            if broadcast_id:
                info = 'Broadcast successfully saved'
            else:
                info = 'Message queued for delivery'
            messages.info(request, info)
            return HttpResponseRedirect(reverse('broadcast-schedule'))
    else:
        form = BroadcastForm(instance=broadcast)
    broadcasts = Broadcast.objects.exclude(schedule_frequency__isnull=True)
    context = {
        'form': form,
        'broadcasts': broadcasts.order_by('date'),
    }
    return render_to_response('broadcast/send_message.html', context,
                              RequestContext(request))


@login_required
@transaction.commit_on_success
def delete_broadcast(request, broadcast_id):
    broadcast = get_object_or_404(Broadcast, pk=broadcast_id)
    if request.method == 'POST':
        # disable broadcast to preserve any foreign keys
        broadcast.schedule_frequency = None
        broadcast.save()
        messages.info(request, 'Broadcast successfully deleted')
        return HttpResponseRedirect(reverse('broadcast-schedule'))
    context = {'broadcast': broadcast}
    return render_to_response('broadcast/delete.html', context,
                              RequestContext(request))


@login_required
def schedule(request):
    broadcasts = Broadcast.objects.exclude(schedule_frequency__isnull=True)
    broadcasts = broadcasts.annotate(recipients=Count('groups__contacts', distinct=True))
    context = {
        'broadcasts': broadcasts.order_by('date'),
    }
    return render_to_response('broadcast/schedule.html', context,
                              RequestContext(request))


@login_required
def list_messages(request):
    messages = BroadcastMessage.objects.select_related()
    context = {
        'broadcast_messages': messages,
    }
    return render_to_response('broadcast/messages.html', context,
                              RequestContext(request))


@login_required
def forwarding(request):
    context = {
        'rules': ForwardingRule.objects.all(),
    }
    return render_to_response('broadcast/forwarding.html', context,
                              RequestContext(request))


@login_required
def create_edit_rule(request, rule_id=None):
    rule = None
    if rule_id:
        rule = get_object_or_404(ForwardingRule, pk=rule_id)
    if request.method == 'POST':
        form = ForwardingRuleForm(request.POST, instance=rule)
        if form.is_valid():
            form.save()
            messages.info(request, "Forwarding Rule saved successfully")
            return redirect('broadcast-forwarding')
    else:
        form = ForwardingRuleForm(instance=rule)
    context = {
        'form': form,
        'rule': rule,
    }
    return render_to_response('broadcast/create_edit_rule.html', context,
                              context_instance=RequestContext(request))


@login_required
def delete_rule(request, rule_id):
    rule = get_object_or_404(ForwardingRule, pk=rule_id)
    if request.method == 'POST':
        rule.delete()
        messages.info(request, 'Forwarding Rule successfully deleted')
        return redirect('broadcast-forwarding')
    context = {'rule': rule}
    return render_to_response('broadcast/delete_rule.html', context,
                              RequestContext(request))

@login_required
def dashboard(request):
    today = datetime.date.today()
    report_date = today
    initial = {'report_year': report_date.year, 'report_month': report_date.month}
    form = ReportForm(request.GET or None, initial=initial)
    if form.is_valid():
        report_year = form.cleaned_data.get('report_year') or report_date.year
        report_month = form.cleaned_data.get('report_month') or report_date.month
        last_day = calendar.monthrange(report_year, report_month)[1]
        report_date = datetime.date(report_year, report_month, last_day)
    start_date = datetime.date(report_date.year, report_date.month, 1)
    end_date = report_date
    context = usage_report_context(start_date, end_date)
    context['report_date'] = report_date
    context['report_form'] = form
    # Identify patients whose wisepill devices' batteries' levels are low, but known
    context['low_battery_patients'] = Patient.objects.\
              filter(batterystrength__lte=WISEPILL_LOW_BATTERY).\
              exclude(batterystrength=-1)
    # Graph data 
    return render_to_response('broadcast/dashboard.html', context,
                              RequestContext(request))


def usage_report_context(start_date, end_date):
    # Get forwarding rule data
    named_rules = ForwardingRule.objects.filter(
        ~Q(Q(label__isnull=True) | Q(label=u"")),
        ~Q(Q(rule_type__isnull=True) | Q(rule_type=u"")),
    )
    # This count includes all queued, sent and error messages from this broadcast
    broadcasts = Broadcast.objects.filter(
        date_created__range=(start_date, end_date),
        schedule_frequency='one-time',
        forward__in=named_rules
    ).select_related('rule').annotate(message_count=Count('messages'))
    rule_data = {}
    for rule in named_rules:
        data = rule_data.get(rule.rule_type, {})
        label_data = data.get(rule.label, [0, 0])
        data[rule.label] = label_data   
        rule_data[rule.rule_type] = data
    for broadcast in broadcasts:
        rule = broadcast.forward
        data = rule_data.get(rule.rule_type, {})
        label_data = data.get(rule.label, [0, 0])
        label_data[0] += 1
        label_data[1] += broadcast.message_count
        data[rule.label] = label_data   
        rule_data[rule.rule_type] = data

    # Get patient reminder data
    confirmed_count = SentNotification.objects.confirmed_for_range(
        start_date, end_date).count()
    unconfirmed_count = SentNotification.objects.unconfirmed_for_range(
        start_date, end_date).count()
    total_reminders = confirmed_count + unconfirmed_count

    # Get total incoming/outgoing data
    incoming_count = Message.objects.filter(
        date__range=(start_date, end_date),
        direction='I'
    ).count()
    outgoing_count = Message.objects.filter(
        date__range=(start_date, end_date),
        direction='O'
    ).count()
    total_messages = incoming_count + outgoing_count

    context = {
        'rule_data': rule_data,
        'confirmed_count': confirmed_count,
        'unconfirmed_count': unconfirmed_count,
        'total_reminders': total_reminders,
        'confirm_percent': confirmed_count * 100.0 / total_reminders if total_reminders else 100.0,
        'incoming_count': incoming_count,
        'outgoing_count': outgoing_count,
        'total_messages': total_messages,
    }
    return context


@login_required
def report_graph_data(request):
    today = datetime.date.today()
    report_date = today
    initial = {'report_year': report_date.year, 'report_month': report_date.month}
    form = ReportForm(request.GET or None, initial=initial)
    if form.is_valid():
        report_year = form.cleaned_data.get('report_year') or report_date.year
        report_month = form.cleaned_data.get('report_month') or report_date.month
        last_day = calendar.monthrange(report_year, report_month)[1]
        report_date = datetime.date(report_year, report_month, last_day)
    data = []
    start_date = datetime.date(report_date.year, report_date.month, 1)
    end_date = report_date
    incoming_count = Message.objects.filter(
        date__range=(start_date, end_date),
        direction='I'
    ).count()
    outgoing_count = Message.objects.filter(
        date__range=(start_date, end_date),
        direction='O'
    ).count()
    row = [end_date.isoformat(), incoming_count, outgoing_count]
    data.append(row)
    for i in range(1, 7):
        month = report_date.month - i
        year = report_date.year
        if month <= 0:
            month += 12
            year -= 1
        last_day = calendar.monthrange(year, month)[1]
        start_date = datetime.date(year, month, 1)
        end_date = datetime.date(year, month, last_day)
        incoming_count = Message.objects.filter(
            date__range=(start_date, end_date),
            direction='I'
        ).count()
        outgoing_count = Message.objects.filter(
            date__range=(start_date, end_date),
            direction='O'
        ).count()
        row = [end_date.isoformat(), incoming_count, outgoing_count]
        data.append(row)
    return HttpResponse(json.dumps(data), mimetype='application/json')


@login_required
def last_messages(request):
    groups = []
    if request.GET:
        form = RecentMessageForm(request.GET)
        if form.is_valid():
            groups = form.cleaned_data.get('groups', [])
    recent = Broadcast.objects.exclude(
        Q(schedule_frequency__isnull=True) | Q(forward__isnull=False)
    )
    if groups:
        recent = recent.filter(groups__in=groups)
    confirmation_group = settings.DEFAULT_CONFIRMATIONS_GROUP_NAME
    if not (groups and confirmation_group in [g.name for g in groups]):
        # Don't include messages to the confirmation group unless
        # explicitly included since it will include all the forwarded confirmations
        recent = recent.exclude(groups__name=confirmation_group)
    recent = recent.order_by('-date').values_list('body', flat=True).distinct()[:10]
    data = {
        'groups': u', '.join([group.name for group in groups]),
        'messages': list(recent)
    }
    return HttpResponse(json.dumps(data), mimetype='application/json')


