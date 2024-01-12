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

STACK_TRACE = f"""
An exception occured while executing a celery task
Traceback (most recent call last):
  File "/usr/local/lib/python3.11/site-packages/celery/app/trace.py", line 477, in trace_task
    R = retval = fun(*args, **kwargs)
                 ^^^^^^^^^^^^^^^^^^^^
  File "/etc/app/common/custom_celery_tasks/tests/test_log_exception_on_failure_task.py", line 28, in my_task
    raise ValueError(EXCEPTION_MSG)
Exception: {EXCEPTION_MSG}
"""


def test_log_exception_on_failure_task_logs_stack_trace_on_task_failure(caplog):
    @shared_log_exception_on_failure_task
    def my_task():
        raise ValueError(EXCEPTION_MSG)

    @shared_task(base=LogExceptionOnFailureTask)
    def my_task_two():
        raise ValueError(EXCEPTION_MSG)

    with pytest.raises(ValueError):
        my_task.apply().get()
        assert STACK_TRACE in caplog.text

    caplog.clear()

    with pytest.raises(ValueError):
        my_task_two.apply().get()
        assert STACK_TRACE in caplog.text
