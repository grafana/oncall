import pytest

from common.custom_celery_tasks.dedicated_queue_retry_task import shared_dedicated_queue_retry_task

EXCEPTION_MSG = "my exception"


def test_dedicated_queue_retry_task_logs_stack_trace_on_task_retry_when_using_autoretry_for(caplog):
    @shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=False, max_retries=1)
    def my_task():
        raise ValueError(EXCEPTION_MSG)

    with pytest.raises(ValueError):
        my_task.apply().get()

    assert "Traceback (most recent call last):" in caplog.text
    assert "Retrying celery task" in caplog.text
    assert f"raise ValueError(EXCEPTION_MSG)\nValueError: {EXCEPTION_MSG}" in caplog.text
    caplog.clear()
