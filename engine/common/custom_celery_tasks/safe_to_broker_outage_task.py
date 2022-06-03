from abc import ABC

from celery import Task
from kombu.exceptions import OperationalError

from apps.base.models import FailedToInvokeCeleryTask


class SafeToBrokerOutageTask(Task, ABC):
    """
    Dumps task name and parameters to a database when broker is not available.
    """

    def apply_async(
        self, args=None, kwargs=None, task_id=None, producer=None, link=None, link_error=None, shadow=None, **options
    ):
        try:
            return super().apply_async(args, kwargs, task_id, producer, link, link_error, shadow, **options)
        except OperationalError:
            parameters = {"args": args, "kwargs": kwargs, "options": options}
            FailedToInvokeCeleryTask.objects.create(name=self.name, parameters=parameters)
