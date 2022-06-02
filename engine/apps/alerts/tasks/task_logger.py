import logging

from celery.utils.log import get_task_logger

task_logger = get_task_logger(__name__)
task_logger.setLevel(logging.DEBUG)
