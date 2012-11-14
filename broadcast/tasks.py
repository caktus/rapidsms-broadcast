from celery.registry import tasks
from celery.task import Task

from broadcast.app import scheduler_callback


class BroadcastCronTask(Task):
    def run(self):
        scheduler_callback()


tasks.register(BroadcastCronTask)
