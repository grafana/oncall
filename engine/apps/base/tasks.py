from django.db import transaction

from apps.base.models import FailedToInvokeCeleryTask
from common.custom_celery_tasks import shared_dedicated_queue_retry_task
from common.utils import batch_queryset


@shared_dedicated_queue_retry_task
def process_failed_to_invoke_celery_tasks():
    task_pks = FailedToInvokeCeleryTask.objects.filter(is_sent=False).values_list("pk", flat=True)

    batches = batch_queryset(task_pks)
    for idx, batch in enumerate(batches):
        countdown = idx * 60
        process_failed_to_invoke_celery_tasks_batch.apply_async((list(batch),), countdown=countdown)


@shared_dedicated_queue_retry_task
def process_failed_to_invoke_celery_tasks_batch(task_pks):
    sent_task_pks = []
    with transaction.atomic():
        for task in FailedToInvokeCeleryTask.objects.filter(pk__in=task_pks, is_sent=False).select_for_update():
            try:
                task.send()
            except Exception:
                continue

            sent_task_pks.append(task.pk)

        FailedToInvokeCeleryTask.objects.filter(pk__in=sent_task_pks).update(is_sent=True)
