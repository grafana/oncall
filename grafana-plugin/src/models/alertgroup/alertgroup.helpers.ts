import { User } from 'models/user/user.types';
import { makeRequest } from 'network/network';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { onCallApi } from 'network/oncall-api/http-client';

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

  static getSearchResult = (store: AlertGroupStore, query = '') => {
    if (!store.searchResult[query]) {
      return undefined;
    }
    return store.searchResult[query].map((id: ApiSchemas['AlertGroup']['pk']) => store.items[id]);
  };

  static async getAlertGroupsForIntegration(integrationId: ApiSchemas['AlertReceiveChannel']['id']) {
    // TODO: check if passing array as query param works ok because previously we passed string
    const {
      data: { results },
    } = await onCallApi().GET('/alertgroups/', { params: { query: { integration: [integrationId] } } });
    return results;
  }

  static async getAlertsFromGroup(pk: ApiSchemas['AlertGroup']['pk']) {
    return (await onCallApi().GET('/alertgroups/{id}/', { params: { path: { id: pk } } })).data;
  }

  static async resolve(id: ApiSchemas['AlertGroup']['pk'], delay: number) {
    await onCallApi().POST('/alertgroups/{id}/silence/', { params: { path: { id } }, body: { delay } });
  }

  static async unresolve(id: ApiSchemas['AlertGroup']['pk']) {
    await onCallApi().POST('/alertgroups/{id}/unresolve/', { params: { path: { id } } });
  }

  static async acknowledge(id: ApiSchemas['AlertGroup']['pk']) {
    await onCallApi().POST('/alertgroups/{id}/acknowledge/', { params: { path: { id } } });
  }

  static async unacknowledge(id: ApiSchemas['AlertGroup']['pk']) {
    await onCallApi().POST('/alertgroups/{id}/unacknowledge/', { params: { path: { id } } });
  }

  static async silence(id: ApiSchemas['AlertGroup']['pk'], delay: number) {
    await onCallApi().POST('/alertgroups/{id}/silence/', { params: { path: { id } }, body: { delay } });
  }

  static async unsilence(id: ApiSchemas['AlertGroup']['pk']) {
    await onCallApi().POST('/alertgroups/{id}/unsilence/', { params: { path: { id } } });
  }

  static async bulkAction(data: ApiSchemas['AlertGroupBulkActionRequest']) {
    return (await onCallApi().POST('/alertgroups/bulk_action/', { params: {}, body: data })).data;
  }

  static async renderPreview(id: ApiSchemas['AlertGroup']['pk'], template_name: string, template_body: string) {
    return (
      await onCallApi().POST('/alertgroups/{id}/preview_template/', {
        params: { path: { id } },
        body: { template_name, template_body },
      })
    ).data;
  }

  static getAlertSearchResult(store: AlertGroupStore, query: string) {
    const result = store.alertsSearchResult[query];
    if (!result) {
      return {};
    }

    return {
      prev: result.prev,
      next: result.next,
      page_size: result.page_size,
      results: result.results.map((pk: ApiSchemas['AlertGroup']['pk']) => store.alerts.get(pk)),
    };
  }

  static async getPayloadForIncident(pk: ApiSchemas['AlertGroup']['pk']) {
    return await makeRequest(`/alerts/${pk}`, {});
  }

  static async unpageUser(id: ApiSchemas['AlertGroup']['pk'], userId: User['pk']) {
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
