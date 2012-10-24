from threadless_router.router import Router

from celery.task import Task
from celery.registry import tasks

from aremind.apps.broadcast.app import scheduler_callback


class BroadcastCronTask(Task):
    def run(self):
        router = Router()
        scheduler_callback(router)


tasks.register(BroadcastCronTask)
