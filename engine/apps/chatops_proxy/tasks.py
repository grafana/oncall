from celery.utils.log import get_task_logger
from django.conf import settings

from common.custom_celery_tasks import shared_dedicated_queue_retry_task

from .client import ChatopsProxyAPIClient, ChatopsProxyAPIException

task_logger = get_task_logger(__name__)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=100,
)
def register_oncall_tenant_async(**kwargs):
    service_tenant_id = kwargs.get("service_tenant_id")
    cluster_slug = kwargs.get("cluster_slug")
    service_type = kwargs.get("service_type")
    stack_id = kwargs.get("stack_id")

    client = ChatopsProxyAPIClient(settings.ONCALL_GATEWAY_URL, settings.ONCALL_GATEWAY_API_TOKEN)
    try:
        client.register_tenant(service_tenant_id, cluster_slug, service_type, stack_id)
    except ChatopsProxyAPIException as api_exc:
        task_logger.error(
            f'msg="Failed to register OnCall tenant: {api_exc.msg}" service_tenant_id={service_tenant_id} cluster_slug={cluster_slug}'
        )
        if api_exc.status == 409:
            # 409 Indicates that it's impossible to register tenant, because tenant already registered.
            # Not retrying in this case, because manual conflict-resolution needed.
            return
        else:
            # Otherwise keep retrying task
            raise api_exc
    except Exception as e:
        # Keep retrying task for any other exceptions too
        task_logger.error(
            f"Failed to register OnCall tenant: {e}  service_tenant_id={service_tenant_id} cluster_slug={cluster_slug}"
        )
        raise e


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=100,
)
def unregister_oncall_tenant_async(**kwargs):
    service_tenant_id = kwargs.get("service_tenant_id")
    cluster_slug = kwargs.get("cluster_slug")
    service_type = kwargs.get("service_type")

    client = ChatopsProxyAPIClient(settings.ONCALL_GATEWAY_URL, settings.ONCALL_GATEWAY_API_TOKEN)
    try:
        client.unregister_tenant(service_tenant_id, cluster_slug, service_type)
    except ChatopsProxyAPIException as api_exc:
        if api_exc.status == 400:
            # 400 Indicates that tenant is already deleted
            return
        else:
            # Otherwise keep retrying task
            raise api_exc
    except Exception as e:
        task_logger.error(f"Failed to delete OnCallTenant: {e} service_tenant_id={service_tenant_id}")
        raise e


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=100,
)
def link_slack_team_async(**kwargs):
    service_tenant_id = kwargs.get("service_tenant_id")
    service_type = kwargs.get("service_type")
    slack_team_id = kwargs.get("slack_team_id")
    client = ChatopsProxyAPIClient(settings.ONCALL_GATEWAY_URL, settings.ONCALL_GATEWAY_API_TOKEN)
    try:
        client.link_slack_team(service_tenant_id, slack_team_id, service_type)
    except ChatopsProxyAPIException as api_exc:
        task_logger.error(
            f'msg="Failed to link slack team: {api_exc.msg}" service_tenant_id={service_tenant_id} slack_team_id={slack_team_id}'
        )
        if api_exc.status == 409:
            # Impossible to register tenant, slack workspace already connected to another cluster.
            # Not retrying in this case, because manual conflict-resolution needed.
            return
        else:
            raise api_exc
    except Exception as e:
        task_logger.error(
            f'msg="Failed to link slack team: {e}" service_tenant_id={service_tenant_id} slack_team_id={slack_team_id}'
        )
        raise e


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=100,
)
def unlink_slack_team_async(**kwargs):
    service_tenant_id = kwargs.get("service_tenant_id")
    service_type = kwargs.get("service_type")
    slack_team_id = kwargs.get("slack_team_id")

    client = ChatopsProxyAPIClient(settings.ONCALL_GATEWAY_URL, settings.ONCALL_GATEWAY_API_TOKEN)
    try:
        client.unlink_slack_team(service_tenant_id, slack_team_id, service_type)
    except ChatopsProxyAPIException as api_exc:
        if api_exc.status == 400:
            # 400 Indicates that tenant is already deleted
            return
        else:
            # Otherwise keep retrying task
            raise api_exc
    except Exception as e:
        task_logger.error(
            f'msg="Failed to unlink slack_team: {e}" service_tenant_id={service_tenant_id} slack_team_id={slack_team_id}'
        )
        raise e
