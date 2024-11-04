import typing

from celery import shared_task
from celery.utils.log import get_task_logger

from common.custom_celery_tasks.log_exception_on_failure_task import LogExceptionOnFailureTask

RETRY_QUEUE = "retry"

logger = logger = get_task_logger(__name__)


# You can also make the fields non-required by adding total=False to the TypedDict
# https://stackoverflow.com/a/63550734
class SharedDedicatedQueueRetryTaskParams(typing.TypedDict, total=False):
    autoretry_for: typing.Tuple[type[Exception]]
    dont_autoretry_for: typing.Tuple[type[Exception]]
    retry_backoff: bool
    max_retries: int
    bind: bool


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

def shared_dedicated_queue_retry_task(**kwargs: typing.Unpack[SharedDedicatedQueueRetryTaskParams]):
    return shared_task(base=DedicatedQueueRetryTask, **kwargs)
