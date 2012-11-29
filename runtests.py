#!/usr/bin/env python
import optparse
import sys

from django.conf import settings


if not settings.configured:
    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'rapidsms',
            'rapidsms.contrib.messagelog',
            'broadcast',
            'groups',
            'sorter',
            'pagination',
        ],
        INSTALLED_BACKENDS={
            'mockbackend': {
                'ENGINE': 'rapidsms.tests.harness.backend',
            },
        },
        LOGIN_URL='/account/login/',
        MIDDLEWARE_CLASSES=[
            'django.middleware.common.CommonMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'pagination.middleware.PaginationMiddleware',
        ],
        RAPIDSMS_TABS=[],
        ROOT_URLCONF='broadcast.tests.urls',
        SITE_ID=1,
        SECRET_KEY='this-is-just-for-tests-so-not-that-secret',
        SORTER_ALLOWED_CRITERIA={
            'sort_rules': ['id', 'keyword', 'source', 'dest', 'message', 'rule_type', 'label'],
            'sort_broadcasts': ['id', 'date', 'schedule_frequency', 'body'],
            'sort_messages': ['broadcast__id', 'broadcast__body', 'date_created', 'status', 'recipient', 'date_sent'],
        },
        TEMPLATE_CONTEXT_PROCESSORS=[
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
            'django.core.context_processors.request',
            'django.core.context_processors.static',
        ],
    )


from django.test.utils import get_runner


def runtests():
    parser = optparse.OptionParser()
    _, tests = parser.parse_args()
    tests = tests or ['broadcast']

    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=1, interactive=True, failfast=False)
    sys.exit(test_runner.run_tests(tests))


if __name__ == '__main__':
    runtests()
