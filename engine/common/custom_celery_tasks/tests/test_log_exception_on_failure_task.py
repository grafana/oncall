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


def _generate_stack_trace(line_number, task_name):
    return (
        "An exception occured while executing a celery task\nTraceback (most recent call last):\n  "
        'File "/usr/local/lib/python3.11/site-packages/celery/app/trace.py", line 477, in trace_task\n    '
        "R = retval = fun(*args, **kwargs)\n                 ^^^^^^^^^^^^^^^^^^^^\n  "
        f'File "/etc/app/common/custom_celery_tasks/tests/test_log_exception_on_failure_task.py", line {line_number}'
        f", in {task_name}\n    raise ValueError(EXCEPTION_MSG)\nValueError: {EXCEPTION_MSG}"
    )


def test_log_exception_on_failure_task_logs_stack_trace_on_task_failure(caplog):
    @shared_log_exception_on_failure_task
    def my_task():
        raise ValueError(EXCEPTION_MSG)

    @shared_task(base=LogExceptionOnFailureTask)
    def my_task_two():
        raise ValueError(EXCEPTION_MSG)

    with pytest.raises(ValueError):
        my_task.apply().get()
    assert _generate_stack_trace("28", "my_task") in caplog.text

    caplog.clear()

    with pytest.raises(ValueError):
        my_task_two.apply().get()
    assert _generate_stack_trace("32", "my_task_two") in caplog.text
