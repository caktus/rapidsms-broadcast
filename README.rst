rapidsms-broadcast
==================

rapidsms-broadcast integrates with the RapidSMS framework and allows you to
send scheduled broadcast messages to certain groups of Contacts.


Getting Started
---------------

To add rapidsms-broadcast to an existing RapidSMS project, add it and its
dependencies to your installed apps::

    INSTALLED_APPS = [
        ...
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'rapidsms',
        'rapidsms.contrib.messagelog',
        'groups',
        'broadcast',
        'pagination',
        'sorter',
        ...
    ]

In addition to the default middleware classes, be sure to include pagination
middleware::

    MIDDLEWARE_CLASSES = [
        ...
        'pagination.middleware.PaginationMiddleware',
        ...
    ]

Configure django_sorter::

    SORTER_ALLOWED_CRITERIA = {
        'sort_rules': ['id', 'keyword', 'source', 'dest', 'message', 'rule_type', 'label'],
        'sort_broadcasts': ['id', 'date', 'schedule_frequency', 'body'],
        'sort_messages': ['broadcast__id', 'broadcast__body', 'date_created', 'status', 'recipient', 'date_sent'],
    }

Add broadcast URLs to your urlconf::

    urlpatterns += patterns('',
        (r'^broadcast/', include('broadcast.urls')),
    )

Optionally, add a link to broadcast in your ``RAPIDSMS_TABS`` setting::

    RAPIDSMS_TABS += [
        ('broadcast.views.send_message', 'Send Broadcast'),
    ]

Finally, run syncdb or migrate::

    python manage.py migrate broadcast



Running the Tests
-----------------

You can run the tests via::

    python runtests.py

If you would like to run specific test(s), specify them as arguments to the
command::

    python runtests.py broadcast.BroadcastAppTest.test_queue_creation


License
-------

rapidsms-broadcast is released under the BSD License. See the
`LICENSE <https://github.com/caktus/rapidsms-broadcast/blob/master/LICENSE>`_
file for more details.


Contributing
------------

If you think you've found a bug or are interested in contributing to this
project check out `rapidsms-broadcast on Github
<https://github.com/caktus/rapidsms-broadcast>`_.

Development sponsored by `Caktus Consulting Group, LLC
<http://www.caktusgroup.com/services>`_.
