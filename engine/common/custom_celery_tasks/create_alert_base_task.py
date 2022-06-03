from abc import ABC

from common.custom_celery_tasks.dedicated_queue_retry_task import DedicatedQueueRetryTask
from common.custom_celery_tasks.safe_to_broker_outage_task import SafeToBrokerOutageTask


class CreateAlertBaseTask(SafeToBrokerOutageTask, DedicatedQueueRetryTask, ABC):
    pass
