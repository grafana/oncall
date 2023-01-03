from unittest.mock import patch

import pytest
from django.conf import settings
from django.test.utils import override_settings
from django.utils import timezone

from apps.grafana_plugin.tasks.sync import run_organization_sync


class SyncOrganization(object):
    called = False
    org = None

    def do_sync_organization(self, org):
        self.called = True
        self.org = org

    def reset(self):
        self.called = False
        self.org = None


class TestGcomAPIClient:
    called = False
    info = None
    status = None

    STACK_STATUS_ACTIVE = "active"

    def reset(self):
        self.called = False
        self.info = None
        self.status = None

    def set_info(self, info):
        self.info = info

    def set_status(self, status):
        self.status = status

    def get_instance_info(self, stack_id: str):
        self.called = True
        return self.info


@pytest.mark.django_db
def test_sync_organization_skip(
    make_organization,
    make_token_for_organization,
):
    organization = make_organization()
    syncer = SyncOrganization()
    with patch("apps.grafana_plugin.tasks.sync.sync_organization", new=lambda org: syncer.do_sync_organization(org)):
        run_organization_sync(organization.id, True)  # Call for existing org (forced)
        assert syncer.called and syncer.org == organization
        syncer.reset()

        run_organization_sync(123321, True)  # Not called for non-existing org
        assert not syncer.called and not syncer.org
        syncer.reset()

        run_organization_sync(organization.id, False)  # Call for new org
        assert syncer.called and syncer.org == organization
        syncer.reset()

        organization.last_time_synced = timezone.now()
        organization.save(update_fields=["last_time_synced"])
        run_organization_sync(organization.id, False)  # Not called for recently synced org
        assert not syncer.called and not syncer.org
        syncer.reset()


@override_settings(GRAFANA_COM_API_TOKEN="TestGrafanaComToken")
@override_settings(LICENSE=settings.CLOUD_LICENSE_NAME)
@pytest.mark.django_db
def test_sync_organization_skip_cloud(
    make_organization,
    make_token_for_organization,
):
    organization = make_organization()
    syncer = SyncOrganization()
    test_client = TestGcomAPIClient()

    with patch("apps.grafana_plugin.tasks.sync.sync_organization", new=lambda org: syncer.do_sync_organization(org)):
        with patch("apps.grafana_plugin.tasks.sync.GcomAPIClient", new=lambda api_token: test_client):
            test_client.info = {"status": "active"}
            run_organization_sync(organization.id, False)  # Called since instance info is active in cloud
            assert test_client.called and syncer.called and syncer.org == organization
            syncer.reset()
            test_client.reset()

            test_client.info = {"status": "paused"}
            run_organization_sync(organization.id, False)  # Not called since status != active in cloud
            assert test_client.called and not syncer.called and not syncer.org
            syncer.reset()
            test_client.reset()

            run_organization_sync(organization.id, False)  # Not called since status was none in cloud
            assert test_client.called and not syncer.called and not syncer.org
            syncer.reset()
            test_client.reset()
