from celery import Task, shared_task
from celery.utils.log import get_task_logger

logger = logger = get_task_logger(__name__)


class LogExceptionOnFailureTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.exception("An exception occured while executing a celery task", exc_info=exc)
        super().on_failure(exc, task_id, args, kwargs, einfo)


def shared_log_exception_on_failure_task(*args, **kwargs):
    return shared_task(*args, base=LogExceptionOnFailureTask, **kwargs)
