from celery import shared_task
from celery.utils.log import get_task_logger

from common.custom_celery_tasks.log_exception_on_failure_task import LogExceptionOnFailureTask

RETRY_QUEUE = "retry"

logger = logger = get_task_logger(__name__)


class DedicatedQueueRetryTask(LogExceptionOnFailureTask):
    """
    Custom task sends all retried task to the dedicated retry queue.
    It is needed to not to overload regular (high, medium, low) queues with retried tasks.
    """

    def retry(
        self, args=None, kwargs=None, exc=None, throw=True, eta=None, countdown=None, max_retries=None, **options
    ):
        logger.warning("Retrying celery task", exc_info=exc)

        # Just call retry with queue argument
        return super().retry(
            args=args,
            kwargs=kwargs,
            exc=exc,
            throw=throw,
            eta=eta,
            countdown=countdown,
            max_retries=max_retries,
            queue=RETRY_QUEUE,
            **options,
        )


def shared_dedicated_queue_retry_task(*args, **kwargs):
    return shared_task(*args, base=DedicatedQueueRetryTask, **kwargs)
