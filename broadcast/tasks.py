from rapidsms.router import get_router

from celery.registry import tasks
from celery.task import Task

from broadcast.app import scheduler_callback


class BroadcastCronTask(Task):
    def run(self):
        router = get_router() 
        scheduler_callback(router)


tasks.register(BroadcastCronTask)
