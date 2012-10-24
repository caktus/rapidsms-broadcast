/* broadcast.js
 * Javascript form functionality for aremind.apps.broadcast RapidSMS app
 */
$(document).ready(function() {
    jQuery.ajaxSettings.traditional = true;
    $('.datetimepicker').datetimepicker();
    $('.multiselect').multiselect({header: false, selectedList: 3});
    
    var span1 = $('<span>').attr('id', 'count').text(0);
    var span2 = $('<span>').text(' characters remaining');
    var counter = $('<div>').addClass('counter').append(span1).append(span2);
    $('#id_body').before(counter);
    $('#id_body').NobleCount('#count', {
        on_negative: 'go_red',
	    on_positive: 'go_green'
    });

    var date_row = $('#id_date').parents('tr').addClass('date-row');
    var frequency_row = $('#id_schedule_frequency').parents('tr').addClass('frequency-row');
    var end_date_row = $('#id_schedule_end_date').parents('tr').addClass('end-date-row');
    var weekdays_row = $('#id_weekdays').parents('tr').addClass('weekdays-row');
    var months_row = $('#id_months').parents('tr').addClass('months-row');
    var body_row = $('#id_body').parents('tr').addClass('body-row');

    function refresh_broadcast_form() {
        var send = $('#id_when').val();
        var frequency = $('#id_schedule_frequency').val();
        if (send == 'now') {
            $(date_row).hide();
            $(frequency_row).hide();
            $(end_date_row).hide();
            $(weekdays_row).hide();
            $(months_row).hide();
        } else {
            $(frequency_row).show();
            if (frequency == 'one-time') {
                $(date_row).show();
                $(end_date_row).hide();
                $(weekdays_row).hide();
                $(months_row).hide();
            } else if (frequency == 'daily') {
                $(end_date_row).show();
                $(weekdays_row).hide();
                $(months_row).hide();
            } else if (frequency == 'weekly') {
                $(weekdays_row).show();
                $(end_date_row).show();
                $(months_row).hide();
            } else if (frequency == 'monthly') {
                $(months_row).show();
                $(end_date_row).show();
                $(weekdays_row).hide();
            } else if (frequency == 'yearly') {
                $(end_date_row).show();
                $(months_row).hide();
                $(weekdays_row).hide();
            }
        }
    }
    refresh_broadcast_form();

    $('#id_when').change(function() {
        refresh_broadcast_form();
    });
    $('#id_schedule_frequency').change(function() {
        refresh_broadcast_form();
    });

    var messageUrl = $('#message-data').attr('href');
    function queryMessages() {
        var now = new Date().getTime();
        var groups = getSelected();
        $.getJSON(messageUrl, {groups: groups, timestamp: now}, showMessages);
    }

    function getSelected() {
        return $('#id_groups').multiselect('getChecked').map(function(){
            return this.value;	
        }).get();
    }

    queryMessages();
    
    $('#id_groups').bind("multiselectclick", queryMessages);

    function showMessages(data) {
        $('#message-data').remove();
        $('.message-list ul.message-data').remove();
        var list = $('<ul>').addClass('message-data');
        var groups = data.groups;
        $('.message-list .groups').remove();
        if (groups) {            
            $('.message-list').append($('<p>').addClass('groups').text('Sent to ' + groups));
        }
        var messages = data.messages;
        if (messages.length) {
            $.each(messages, function(i, r) {
                var item = $('<li>').addClass('message-item').attr('title', r).text(r + ' ');
                var link = $('<a>').addClass('copy').attr('title', "Copy message body").text('Copy');
                link.click(function(e) {
                    e.preventDefault();
                    var msg = $(this).closest('.message-item').attr('title');
                    $('#id_body').val(msg);
                    $('#id_body').keyup();
                });
                item.append(link);
                list.append(item);
            });
        } else {
            var item = $('<li>').addClass('message-item').text('No recent messages');
            list.append(item);
        }
        $('.message-list').append(list);
    }

    $('#tabs li.app-sendamessage').addClass('active');
});

