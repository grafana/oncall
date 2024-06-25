import { ActionKey } from 'models/loader/action-keys';
import { makeRequest } from 'network/network';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { onCallApi } from 'network/oncall-api/http-client';
import { AutoLoadingState } from 'utils/decorators';

import { AlertGroupStore } from './alertgroup';

export class AlertGroupHelper {
  static async attachAlert(pk: ApiSchemas['AlertGroup']['pk'], rootPk: ApiSchemas['AlertGroup']['pk']) {
    return await onCallApi().POST('/alertgroups/{id}/attach/', {
      params: { path: { id: pk } },
      body: { root_alert_group_pk: rootPk },
    });
  }

  static async unattachAlert(pk: ApiSchemas['AlertGroup']['pk']) {
    return await onCallApi().POST('/alertgroups/{id}/unattach/', {
      params: { path: { id: pk } },
    });
  }

  static async getAlertGroupsForIntegration(integrationId: ApiSchemas['AlertReceiveChannel']['id']) {
    const {
      data: { results },
    } = await onCallApi().GET('/alertgroups/', { params: { query: { integration: [integrationId] } } });
    return results;
  }

  static async getAlertsFromGroup(pk: ApiSchemas['AlertGroup']['pk']) {
    return (await onCallApi().GET('/alertgroups/{id}/', { params: { path: { id: pk } } })).data;
  }

  static async bulkAction(data: ApiSchemas['AlertGroupBulkActionRequest']) {
    return (await onCallApi().POST('/alertgroups/bulk_action/', { params: {}, body: data })).data;
  }

  @AutoLoadingState(ActionKey.INCIDENTS_BULK_UPDATE)
  static async updateBulkActionAndRefresh(
    data: ApiSchemas['AlertGroupBulkActionRequest'],
    alertGroupStore: AlertGroupStore,
    onFinally?: () => void
  ) {
    try {
      alertGroupStore.setLiveUpdatesPaused(true);

      await AlertGroupHelper.bulkAction(data);

      // pull new data
      await alertGroupStore.fetchAlertGroups();
    } finally {
      alertGroupStore.setLiveUpdatesPaused(false);

      onFinally?.();
    }
  }

  static async renderPreview(id: ApiSchemas['AlertGroup']['pk'], template_name: string, template_body: string) {
    return (
      await onCallApi().POST('/alertgroups/{id}/preview_template/', {
        params: { path: { id } },
        body: { template_name, template_body },
      })
    ).data;
  }

  static getAlertSearchResult(store: AlertGroupStore) {
    const result = store.alertsSearchResult;
    if (!result) {
      return {};
    }

    return {
      prev: result.prev,
      next: result.next,
      page_size: result.page_size,
      results: result.results?.map((pk: ApiSchemas['AlertGroup']['pk']) => store.alerts.get(pk)),
    };
  }

  static async getPayloadForIncident(pk: ApiSchemas['AlertGroup']['pk']) {
    return await makeRequest(`/alerts/${pk}`, {});
  }

  static async unpageUser(id: ApiSchemas['AlertGroup']['pk'], userId: ApiSchemas['User']['pk']) {
    return (
      await onCallApi().POST('/alertgroups/{id}/unpage_user/', { params: { path: { id } }, body: { user_id: userId } })
    ).data;
  }

  static async resetTableSettings() {
    return await makeRequest('/alertgroup_table_settings/reset', { method: 'POST' });
  }

  static async loadLabelsKeys() {
    return (await onCallApi().GET('/alertgroups/labels/keys/', undefined)).data;
  }

  static async loadValuesForLabelKey(key: ApiSchemas['LabelKey']['id'], search = '') {
    if (!key) {
      return { key: undefined, values: [] };
    }

    const result = (await onCallApi().GET('/alertgroups/labels/id/{key_id}', { params: { path: { key_id: key } } }))
      .data;

    const filteredValues = result.values.filter((v: ApiSchemas['LabelValue']) =>
      v.name.toLowerCase().includes(search.toLowerCase())
    );

    return { ...result, values: filteredValues };
  }
}
