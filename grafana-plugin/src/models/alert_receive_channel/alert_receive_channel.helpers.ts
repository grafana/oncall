import { ChannelFilter } from 'models/channel_filter/channel_filter.types';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
import { makeRequest } from 'network';
import { ApiSchemas } from 'network/oncall-api/api.types';
import onCallApi from 'network/oncall-api/http-client';
import { SelectOption } from 'state/types';
import { showApiError } from 'utils';

import { AlertReceiveChannelStore } from './alert_receive_channel';
import { MaintenanceMode } from './alert_receive_channel.types';

export function getAlertReceiveChannelDisplayName(
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

export const getSearchResult = (store: AlertReceiveChannelStore) =>
  store.searchResult
    ? store.searchResult.map(
        (alertReceiveChannelId: ApiSchemas['AlertReceiveChannel']['id']) => store.items?.[alertReceiveChannelId]
      )
    : undefined;

export const getPaginatedSearchResult = (store: AlertReceiveChannelStore) =>
  store.paginatedSearchResult
    ? {
        page_size: store.paginatedSearchResult.page_size,
        count: store.paginatedSearchResult.count,
        results: store.paginatedSearchResult.results?.map(
          (alertReceiveChannelId: ApiSchemas['AlertReceiveChannel']['id']) => store.items?.[alertReceiveChannelId]
        ),
      }
    : undefined;

export const getIntegration = (
  store: AlertReceiveChannelStore,
  alertReceiveChannel: Partial<ApiSchemas['AlertReceiveChannel']>
): SelectOption => {
  return (
    store.alertReceiveChannelOptions &&
    alertReceiveChannel &&
    store.alertReceiveChannelOptions.find(
      (alertReceiveChannelOption: SelectOption) => alertReceiveChannelOption.value === alertReceiveChannel.integration
    )
  );
};

export const deleteAlertReceiveChannel = async (id: ApiSchemas['AlertReceiveChannel']['id']) =>
  (await onCallApi.DELETE('/alert_receive_channels/{id}/', { params: { path: { id } } })).data;

export const getGrafanaAlertingContactPoints = async () => {
  try {
    return (await onCallApi.GET('/alert_receive_channels/contact_points/', undefined)).data;
  } catch (err) {
    // TODO: Move error handling to network layer
    showApiError(err);
    return err;
  }
};

export const connectContactPoint = async (
  alertReceiveChannelId: ApiSchemas['AlertReceiveChannel']['id'],
  datasource_uid: string,
  contact_point_name: string
) =>
  (
    await onCallApi.POST('/alert_receive_channels/{id}/connect_contact_point/', {
      params: { path: { id: alertReceiveChannelId } },
      body: {
        datasource_uid,
        contact_point_name,
      },
    })
  ).data;

export const disconnectContactPoint = async (
  alertReceiveChannelId: ApiSchemas['AlertReceiveChannel']['id'],
  datasource_uid: string,
  contact_point_name: string
) =>
  (
    await onCallApi.POST('/alert_receive_channels/{id}/disconnect_contact_point/', {
      params: { path: { id: alertReceiveChannelId } },
      body: {
        datasource_uid,
        contact_point_name,
      },
    })
  ).data;

export const createContactPoint = async (
  alertReceiveChannelId: ApiSchemas['AlertReceiveChannel']['id'],
  datasource_uid: string,
  contact_point_name: string
) =>
  (
    await onCallApi.POST('/alert_receive_channels/{id}/create_contact_point/', {
      params: { path: { id: alertReceiveChannelId } },
      body: {
        datasource_uid,
        contact_point_name,
      },
    })
  ).data;

export const sendDemoAlert = async (
  id: ApiSchemas['AlertReceiveChannel']['id'],
  payload?: { [key: string]: unknown }
) => {
  try {
    await onCallApi.POST('/alert_receive_channels/{id}/send_demo_alert/', {
      params: { path: { id } },
      body: { demo_alert_payload: payload },
    });
  } catch (err) {
    // TODO: move error handling to network layer
    showApiError(err);
  }
};

export const renderPreview = async (
  id: ApiSchemas['AlertReceiveChannel']['id'],
  template_name: string,
  template_body: string,
  payload: { [key: string]: unknown }
) =>
  (
    await onCallApi.POST('/alertgroups/{id}/preview_template/', {
      params: { path: { id } },
      body: { template_name, template_body, payload },
    })
  ).data;

export const changeTeam = async (id: ApiSchemas['AlertReceiveChannel']['id'], teamId: GrafanaTeam['id']) =>
  (
    await onCallApi.PUT('/alert_receive_channels/{id}/change_team/', {
      params: { path: { id }, query: { team_id: String(teamId) } },
    })
  ).data;

export const migrateChannel = async (id: ApiSchemas['AlertReceiveChannel']['id']) =>
  (await onCallApi.POST('/alert_receive_channels/{id}/migrate/', { params: { path: { id } } })).data;

export const startMaintenanceMode = async (
  id: ApiSchemas['AlertReceiveChannel']['id'],
  mode: MaintenanceMode,
  duration: ApiSchemas['DurationEnum']
) =>
  (
    await onCallApi.POST('/alert_receive_channels/{id}/start_maintenance/', {
      params: { path: { id } },
      body: {
        mode,
        duration,
      },
    })
  ).data;

export const stopMaintenanceMode = async (id: ApiSchemas['AlertReceiveChannel']['id']) =>
  (await onCallApi.POST('/alert_receive_channels/{id}/stop_maintenance/', { params: { path: { id } } })).data;

export const sendDemoAlertToParticularRoute = async (id: ChannelFilter['id']) => {
  await makeRequest(`/channel_filters/${id}/send_demo_alert/`, { method: 'POST' }).catch(showApiError);
};

export const convertRegexpTemplateToJinja2Template = async (id: ChannelFilter['id']) => {
  const result = await makeRequest(`/channel_filters/${id}/convert_from_regex_to_jinja2/`, { method: 'POST' }).catch(
    showApiError
  );
  return result;
};

export const createChannelFilter = async (data: Partial<ChannelFilter>) =>
  await makeRequest('/channel_filters/', {
    method: 'POST',
    data,
  });
