from functools import partial

from celery.utils.log import get_task_logger
from django.conf import settings

from common.custom_celery_tasks import shared_dedicated_queue_retry_task

from .client import ChatopsProxyAPIClient, ChatopsProxyAPIException
from .register_oncall_tenant import register_oncall_tenant

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
    stack_slug = kwargs.get("stack_slug")
    org_id = kwargs.get("org_id")

    # Temporary hack to support both old and new set of arguments
    if org_id:
        from apps.user_management.models import Organization

        try:
            org = Organization.objects.get(pk=org_id)
        except Organization.DoesNotExist:
            task_logger.info(f"register_oncall_tenant_async: organization {org_id} was not found")
            return
        register_func = partial(register_oncall_tenant, org)
    else:
        client = ChatopsProxyAPIClient(settings.ONCALL_GATEWAY_URL, settings.ONCALL_GATEWAY_API_TOKEN)
        register_func = partial(
            client.register_tenant, service_tenant_id, cluster_slug, service_type, stack_id, stack_slug
        )
    try:
        register_func()
    except ChatopsProxyAPIException as api_exc:
        # TODO: remove this check once new upsert tenant api is released
        if api_exc.status == 409:
            # 409 Indicates that it's impossible to register tenant, because tenant already registered.
            # Not retrying in this case, because manual conflict-resolution needed.
            task_logger.info(f"register_oncall_tenant_async: tenant for organization {org_id} already exists")
            return
        else:
            # Otherwise keep retrying task
            task_logger.error(
                f"register_oncall_tenant_async: failed to register tenant for organization {org_id}: {api_exc.msg}"
            )
            raise api_exc
    except Exception as e:
        # Keep retrying task for any other exceptions too
        task_logger.error(f"register_oncall_tenant_async: failed to register tenant for organization {org_id}: {e}")
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


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=0,
)
def start_sync_org_with_chatops_proxy():
    from apps.user_management.models import Organization

    organization_qs = Organization.objects.all()
    organization_pks = organization_qs.values_list("pk", flat=True)

    max_countdown = 12 * 60 * 60  # 12 hours, feel free to adjust
    for idx, organization_pk in enumerate(organization_pks):
        countdown = idx % max_countdown
        sync_org_with_chatops_proxy.apply_async(kwargs={"org_id": organization_pk}, countdown=countdown)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def sync_org_with_chatops_proxy(**kwargs):
    from apps.user_management.models import Organization

    org_id = kwargs.get("org_id")
    task_logger.info(f"sync_org_with_chatops_proxy: started org_id={org_id}")

    try:
        org = Organization.objects.get(pk=org_id)
    except Organization.DoesNotExist:
        task_logger.info(f"sync_org_with_chatops_proxy: organization {org_id} was not found")
        return

    try:
        register_oncall_tenant(org)
    except ChatopsProxyAPIException as api_exc:
        # TODO: once tenants upsert api is released, remove this check
        if api_exc.status == 409:
            task_logger.info(f"sync_org_with_chatops_proxy: tenant for organization {org_id} already exists")
            # 409 Indicates that it's impossible to register tenant, because tenant already registered.
            return
        raise api_exc
