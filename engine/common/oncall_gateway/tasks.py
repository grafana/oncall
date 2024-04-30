from apps.chatops_proxy import tasks as new_tasks
from common.custom_celery_tasks import shared_dedicated_queue_retry_task


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=100,
)
def register_oncall_tenant_async(**kwargs):
    new_tasks.register_oncall_tenant_async.apply_async(
        kwargs=kwargs,
    )


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=100,
)
def unregister_oncall_tenant_async(**kwargs):
    new_tasks.unregister_oncall_tenant_async.apply_async(
        kwargs=kwargs,
    )


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=100,
)
def link_slack_team_async(**kwargs):
    new_tasks.link_slack_team_async.apply_async(
        kwargs=kwargs,
    )


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=100,
)
def unlink_slack_team_async(**kwargs):
    new_tasks.unlink_slack_team_async.apply_async(
        kwargs=kwargs,
    )
