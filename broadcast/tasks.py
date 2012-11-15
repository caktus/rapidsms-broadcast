#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from celery.registry import tasks
from celery.task import Task

from broadcast.app import scheduler_callback


class BroadcastCronTask(Task):
    def run(self):
        scheduler_callback()


tasks.register(BroadcastCronTask)
