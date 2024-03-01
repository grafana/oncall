import { ChannelFilter } from 'models/channel_filter/channel_filter.types';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
import { makeRequest } from 'network/network';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { onCallApi } from 'network/oncall-api/http-client';
import { SelectOption } from 'state/types';
import { showApiError } from 'utils/utils';

import { AlertReceiveChannelStore } from './alert_receive_channel';
import { MaintenanceMode } from './alert_receive_channel.types';

export class AlertReceiveChannelHelper {
  static getAlertReceiveChannelDisplayName(
    alertReceiveChannel?: ApiSchemas['AlertReceiveChannel'],
    withDescription = true
  ) {
    if (!alertReceiveChannel) {
      return '';
    }

    return withDescription && alertReceiveChannel.description
      ? `${alertReceiveChannel.verbal_name} (${alertReceiveChannel.description})`
      : alertReceiveChannel.verbal_name;
  }

  static getSearchResult(store: AlertReceiveChannelStore) {
    return store.searchResult
      ? store.searchResult.map(
          (alertReceiveChannelId: ApiSchemas['AlertReceiveChannel']['id']) => store.items?.[alertReceiveChannelId]
        )
      : undefined;
  }

  static getPaginatedSearchResult(store: AlertReceiveChannelStore) {
    return store.paginatedSearchResult
      ? {
          page_size: store.paginatedSearchResult.page_size,
          count: store.paginatedSearchResult.count,
          results: store.paginatedSearchResult.results?.map(
            (alertReceiveChannelId: ApiSchemas['AlertReceiveChannel']['id']) => store.items?.[alertReceiveChannelId]
          ),
        }
      : undefined;
  }

  static getIntegrationSelectOption(
    store: AlertReceiveChannelStore,
    alertReceiveChannel: Partial<ApiSchemas['AlertReceiveChannel'] | ApiSchemas['FastAlertReceiveChannel']>
  ): SelectOption {
    return (
      store.alertReceiveChannelOptions &&
      alertReceiveChannel &&
      store.alertReceiveChannelOptions.find(
        (alertReceiveChannelOption: SelectOption) => alertReceiveChannelOption.value === alertReceiveChannel.integration
      )
    );
  }

  static async deleteAlertReceiveChannel(id: ApiSchemas['AlertReceiveChannel']['id']) {
    return (await onCallApi().DELETE('/alert_receive_channels/{id}/', { params: { path: { id } } })).data;
  }

  static async getGrafanaAlertingContactPoints() {
    return (await onCallApi().GET('/alert_receive_channels/contact_points/', undefined)).data;
  }

  static async connectContactPoint(
    alertReceiveChannelId: ApiSchemas['AlertReceiveChannel']['id'],
    datasource_uid: string,
    contact_point_name: string
  ) {
    return (
      await onCallApi().POST('/alert_receive_channels/{id}/connect_contact_point/', {
        params: { path: { id: alertReceiveChannelId } },
        body: {
          datasource_uid,
          contact_point_name,
        },
      })
    ).data;
  }

  static async disconnectContactPoint(
    alertReceiveChannelId: ApiSchemas['AlertReceiveChannel']['id'],
    datasource_uid: string,
    contact_point_name: string
  ) {
    return (
      await onCallApi().POST('/alert_receive_channels/{id}/disconnect_contact_point/', {
        params: { path: { id: alertReceiveChannelId } },
        body: {
          datasource_uid,
          contact_point_name,
        },
      })
    ).data;
  }

  static async createContactPoint(
    alertReceiveChannelId: ApiSchemas['AlertReceiveChannel']['id'],
    datasource_uid: string,
    contact_point_name: string
  ) {
    return (
      await onCallApi().POST('/alert_receive_channels/{id}/create_contact_point/', {
        params: { path: { id: alertReceiveChannelId } },
        body: {
          datasource_uid,
          contact_point_name,
        },
      })
    ).data;
  }

  static async sendDemoAlert(id: ApiSchemas['AlertReceiveChannel']['id'], payload?: { [key: string]: unknown }) {
    await onCallApi().POST('/alert_receive_channels/{id}/send_demo_alert/', {
      params: { path: { id } },
      body: { demo_alert_payload: payload },
    });
  }

  static async renderPreview(
    id: ApiSchemas['AlertReceiveChannel']['id'],
    template_name: string,
    template_body: string,
    payload: { [key: string]: unknown }
  ) {
    return (
      await onCallApi().POST('/alert_receive_channels/{id}/preview_template/', {
        params: { path: { id } },
        body: { template_name, template_body, payload },
      })
    ).data;
  }

  static async changeTeam(id: ApiSchemas['AlertReceiveChannel']['id'], teamId: GrafanaTeam['id']) {
    return (
      await onCallApi().PUT('/alert_receive_channels/{id}/change_team/', {
        params: { path: { id }, query: { team_id: String(teamId) } },
      })
    ).data;
  }

  static async migrateChannel(id: ApiSchemas['AlertReceiveChannel']['id']) {
    return (await onCallApi().POST('/alert_receive_channels/{id}/migrate/', { params: { path: { id } } })).data;
  }

  static async startMaintenanceMode(
    id: ApiSchemas['AlertReceiveChannel']['id'],
    mode: MaintenanceMode,
    duration: ApiSchemas['DurationEnum']
  ) {
    return (
      await onCallApi().POST('/alert_receive_channels/{id}/start_maintenance/', {
        params: { path: { id } },
        body: {
          mode,
          duration,
        },
      })
    ).data;
  }

  static async stopMaintenanceMode(id: ApiSchemas['AlertReceiveChannel']['id']) {
    return (await onCallApi().POST('/alert_receive_channels/{id}/stop_maintenance/', { params: { path: { id } } }))
      .data;
  }

  static async sendDemoAlertToParticularRoute(id: ChannelFilter['id']) {
    await makeRequest(`/channel_filters/${id}/send_demo_alert/`, { method: 'POST' }).catch(showApiError);
  }

  static async convertRegexpTemplateToJinja2Template(id: ChannelFilter['id']) {
    const result = await makeRequest(`/channel_filters/${id}/convert_from_regex_to_jinja2/`, { method: 'POST' }).catch(
      showApiError
    );
    return result;
  }

  static async createChannelFilter(data: Partial<ChannelFilter>) {
    return await makeRequest('/channel_filters/', {
      method: 'POST',
      data,
    });
  }
}
