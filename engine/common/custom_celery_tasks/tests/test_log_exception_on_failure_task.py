"""
https://docs.celeryq.dev/en/v5.3.2/userguide/testing.html
"""
import pytest
from celery import shared_task

from common.custom_celery_tasks.log_exception_on_failure_task import (
    LogExceptionOnFailureTask,
    shared_log_exception_on_failure_task,
)

EXCEPTION_MSG = "my exception"


def test_log_exception_on_failure_task_logs_stack_trace_on_task_failure(caplog):
    @shared_log_exception_on_failure_task
    def my_task():
        raise ValueError(EXCEPTION_MSG)

    @shared_task(base=LogExceptionOnFailureTask)
    def my_task_two():
        raise ValueError(EXCEPTION_MSG)

    def _assert_stack_trace_in_log():
        assert "Traceback (most recent call last):" in caplog.text
        assert "An exception occured while executing a celery task" in caplog.text
        assert f"raise ValueError(EXCEPTION_MSG)\nValueError: {EXCEPTION_MSG}" in caplog.text
        caplog.clear()

    with pytest.raises(ValueError):
        my_task.apply().get()
    _assert_stack_trace_in_log()

    with pytest.raises(ValueError):
        my_task_two.apply().get()
    _assert_stack_trace_in_log()
