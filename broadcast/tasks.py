from threadless_router.router import Router

from celery.registry import tasks
from celery.task import Task

from broadcast.app import scheduler_callback


class BroadcastCronTask(Task):
    def run(self):
        router = Router()
        scheduler_callback(router)


tasks.register(BroadcastCronTask)
