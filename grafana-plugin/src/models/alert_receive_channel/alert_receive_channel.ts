import { omit } from 'lodash-es';
import { action, observable } from 'mobx';

import { AlertTemplatesDTO } from 'models/alert_templates';
import { Alert } from 'models/alertgroup/alertgroup.types';
import BaseStore from 'models/base_store';
import { ChannelFilter } from 'models/channel_filter/channel_filter.types';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
import { Heartbeat } from 'models/heartbeat/heartbeat.types';
import { OutgoingWebhook } from 'models/outgoing_webhook/outgoing_webhook.types';
import { makeRequest } from 'network';
import { Mixpanel } from 'services/mixpanel';
import { RootStore } from 'state';
import { move } from 'state/helpers';
import { SelectOption } from 'state/types';
import { showApiError } from 'utils';

import {
  AlertReceiveChannel,
  AlertReceiveChannelOption,
  AlertReceiveChannelCounters,
  ContactPoint,
  MaintenanceMode,
} from './alert_receive_channel.types';

export class AlertReceiveChannelStore extends BaseStore {
  @observable.shallow
  searchResult: Array<AlertReceiveChannel['id']>;

  @observable.shallow
  paginatedSearchResult: { count?: number; results?: Array<AlertReceiveChannel['id']> } = {};

  @observable.shallow
  items: { [id: string]: AlertReceiveChannel } = {};

  @observable.shallow
  counters: { [id: string]: AlertReceiveChannelCounters } = {};

  @observable
  channelFilterIds: { [id: string]: Array<ChannelFilter['id']> } = {};

  @observable.shallow
  channelFilters: { [id: string]: ChannelFilter } = {};

  @observable
  alertReceiveChannelToHeartbeat: {
    [id: string]: Heartbeat['id'];
  } = {};

  @observable.shallow
  actions: { [id: string]: OutgoingWebhook[] } = {};

  @observable.shallow
  alertReceiveChannelOptions: AlertReceiveChannelOption[] = [];

  @observable.shallow
  templates: { [id: string]: AlertTemplatesDTO[] } = {};

  @observable
  connectedContactPoints: { [id: string]: ContactPoint[] } = {};

  constructor(rootStore: RootStore) {
    super(rootStore);

    this.path = '/alert_receive_channels/';
  }

  getSearchResult(_query = '') {
    if (!this.searchResult) {
      return undefined;
    }

    return this.searchResult.map(
      (alertReceiveChannelId: AlertReceiveChannel['id']) => this.items?.[alertReceiveChannelId]
    );
  }

  getPaginatedSearchResult(_query = '') {
    if (!this.paginatedSearchResult) {
      return undefined;
    }

    return {
      count: this.paginatedSearchResult.count,
      results:
        this.paginatedSearchResult.results &&
        this.paginatedSearchResult.results.map(
          (alertReceiveChannelId: AlertReceiveChannel['id']) => this.items?.[alertReceiveChannelId]
        ),
    };
  }

  @action
  async loadItem(id: AlertReceiveChannel['id'], skipErrorHandling = false): Promise<AlertReceiveChannel> {
    const alertReceiveChannel = await this.getById(id, skipErrorHandling);

    // @ts-ignore
    this.items = {
      ...this.items,
      [id]: omit(alertReceiveChannel, 'heartbeat'),
    };

    this.populateHearbeats([alertReceiveChannel]);

    return alertReceiveChannel;
  }

  @action
  async updateItems(query: any = '') {
    const params = typeof query === 'string' ? { search: query } : query;

    const { results } = await makeRequest(this.path, { params });

    this.items = {
      ...this.items,
      ...results.reduce(
        (acc: { [key: number]: AlertReceiveChannel }, item: AlertReceiveChannel) => ({
          ...acc,
          [item.id]: omit(item, 'heartbeat'),
        }),
        {}
      ),
    };

    this.populateHearbeats(results);

    this.searchResult = results.map((item: AlertReceiveChannel) => item.id);

    this.updateCounters();

    return results;
  }

  async updatePaginatedItems(query: any = '', page = 1) {
    const filters = typeof query === 'string' ? { search: query } : query;
    const { count, results } = await makeRequest(this.path, { params: { ...filters, page } });

    this.items = {
      ...this.items,
      ...results.reduce(
        (acc: { [key: number]: AlertReceiveChannel }, item: AlertReceiveChannel) => ({
          ...acc,
          [item.id]: omit(item, 'heartbeat'),
        }),
        {}
      ),
    };

    this.populateHearbeats(results);

    this.paginatedSearchResult = {
      count,
      results: results.map((item: AlertReceiveChannel) => item.id),
    };

    this.updateCounters();

    return results;
  }

  populateHearbeats(alertReceiveChannels: AlertReceiveChannel[]) {
    const heartbeats = alertReceiveChannels.reduce((acc: any, alertReceiveChannel: AlertReceiveChannel) => {
      if (alertReceiveChannel.heartbeat) {
        acc[alertReceiveChannel.heartbeat.id] = alertReceiveChannel.heartbeat;
      }

      return acc;
    }, {});

    this.rootStore.heartbeatStore.items = {
      ...this.rootStore.heartbeatStore.items,
      ...heartbeats,
    };

    const alertReceiveChannelToHeartbeat = alertReceiveChannels.reduce(
      (acc: any, alertReceiveChannel: AlertReceiveChannel) => {
        if (alertReceiveChannel.heartbeat) {
          acc[alertReceiveChannel.id] = alertReceiveChannel.heartbeat.id;
        }

        return acc;
      },
      {}
    );

    this.alertReceiveChannelToHeartbeat = {
      ...this.alertReceiveChannelToHeartbeat,
      ...alertReceiveChannelToHeartbeat,
    };
  }

  @action
  async updateChannelFilters(alertReceiveChannelId: AlertReceiveChannel['id'], isOverwrite = false) {
    const response = await makeRequest(`/channel_filters/`, {
      params: { alert_receive_channel: alertReceiveChannelId },
    });

    const channelFilters = response.reduce(
      (acc: any, channelFilter: ChannelFilter) => ({
        ...acc,
        [channelFilter.id]: channelFilter,
      }),
      {}
    );

    this.channelFilters = {
      ...this.channelFilters,
      ...channelFilters,
    };

    if (isOverwrite) {
      // This is needed because on Move Up/Down/Removal the store no longer reflects the correct state
      this.channelFilters = {
        ...channelFilters,
      };
    }

    this.channelFilterIds = {
      ...this.channelFilterIds,
      [alertReceiveChannelId]: response.map((channelFilter: ChannelFilter) => channelFilter.id),
    };
  }

  @action
  async updateChannelFilter(channelFilterId: ChannelFilter['id']) {
    const response = await makeRequest(`/channel_filters/${channelFilterId}/`, {});

    this.channelFilters = {
      ...this.channelFilters,
      [channelFilterId]: response,
    };
  }

  @action
  async migrateChannel(id: AlertReceiveChannel['id']) {
    return await makeRequest(`/alert_receive_channels/${id}/migrate`, {
      method: 'POST',
    });
  }

  @action
  async createChannelFilter(data: Partial<ChannelFilter>) {
    return await makeRequest('/channel_filters/', {
      method: 'POST',
      data,
    });
  }

  @action
  async saveChannelFilter(channelFilterId: ChannelFilter['id'], data: Partial<ChannelFilter>) {
    const response = await makeRequest(`/channel_filters/${channelFilterId}/`, {
      method: 'PUT',
      data,
    });

    this.channelFilters = {
      ...this.channelFilters,
      [response.id]: response,
    };

    return response;
  }

  @action
  async moveChannelFilterToPosition(
    alertReceiveChannelId: AlertReceiveChannel['id'],
    oldIndex: number,
    newIndex: number
  ) {
    Mixpanel.track('Move ChannelFilter', null);

    const channelFilterId = this.channelFilterIds[alertReceiveChannelId][oldIndex];

    this.channelFilterIds[alertReceiveChannelId] = move(
      this.channelFilterIds[alertReceiveChannelId],
      oldIndex,
      newIndex
    );

    await makeRequest(`/channel_filters/${channelFilterId}/move_to_position/?position=${newIndex}`, { method: 'PUT' });

    this.updateChannelFilters(alertReceiveChannelId, true);
  }

  @action
  async deleteChannelFilter(channelFilterId: ChannelFilter['id']) {
    Mixpanel.track('Delete ChannelFilter', null);

    const channelFilter = this.channelFilters[channelFilterId];

    this.channelFilterIds[channelFilter.alert_receive_channel].splice(
      this.channelFilterIds[channelFilter.alert_receive_channel].indexOf(channelFilterId),
      1
    );

    await makeRequest(`/channel_filters/${channelFilterId}`, {
      method: 'DELETE',
    });

    this.updateChannelFilters(channelFilter.alert_receive_channel, true);
  }

  @action
  async updateAlertReceiveChannelOptions() {
    const response = await makeRequest(`/alert_receive_channels/integration_options/`, {});

    this.alertReceiveChannelOptions = response;
  }

  getIntegration(alertReceiveChannel: Partial<AlertReceiveChannel>): SelectOption {
    return (
      this.alertReceiveChannelOptions &&
      alertReceiveChannel &&
      this.alertReceiveChannelOptions.find(
        (alertReceiveChannelOption: SelectOption) => alertReceiveChannelOption.value === alertReceiveChannel.integration
      )
    );
  }

  @action
  async saveAlertReceiveChannel(id: AlertReceiveChannel['id'], data: Partial<AlertReceiveChannel>) {
    const item = await this.update(id, data);

    this.items = {
      ...this.items,
      [id]: item,
    };
  }

  @action
  async deleteAlertReceiveChannel(id: AlertReceiveChannel['id']) {
    return await this.delete(id);
  }

  @action
  async updateTemplates(alertReceiveChannelId: AlertReceiveChannel['id'], alertGroupId?: Alert['pk']) {
    const response = await makeRequest(`/alert_receive_channel_templates/${alertReceiveChannelId}/`, {
      params: { alert_group_id: alertGroupId },
      withCredentials: true,
    });

    this.templates = {
      ...this.templates,
      [alertReceiveChannelId]: response,
    };
  }

  @action
  async updateItem(id: AlertReceiveChannel['id']) {
    const item = await this.getById(id);

    this.items = {
      ...this.items,
      [id]: item,
    };
  }

  @action
  async saveTemplates(alertReceiveChannelId: AlertReceiveChannel['id'], data: Partial<AlertTemplatesDTO>) {
    const response = await makeRequest(`/alert_receive_channel_templates/${alertReceiveChannelId}/`, {
      method: 'PUT',
      data,
      withCredentials: true,
    });

    this.templates = {
      ...this.templates,
      [alertReceiveChannelId]: response,
    };
  }

  async getGrafanaAlertingContactPoints() {
    return await makeRequest(`${this.path}contact_points/`, {}).catch(showApiError);
  }

  @action
  async updateConnectedContactPoints(alertReceiveChannelId: AlertReceiveChannel['id']) {
    const response = await makeRequest(`${this.path}${alertReceiveChannelId}/connected_contact_points `, {});

    this.connectedContactPoints = {
      ...this.connectedContactPoints,

      [alertReceiveChannelId]: response.reduce((list: ContactPoint[], payload) => {
        payload.contact_points.forEach((contactPoint: { name: string; notification_connected: boolean }) => {
          list.push({
            dataSourceName: payload.name,
            dataSourceId: payload.uid,
            contactPoint: contactPoint.name,
            notificationConnected: contactPoint.notification_connected,
          } as ContactPoint);
        });

        return list;
      }, []),
    };
  }

  async connectContactPoint(
    alertReceiveChannelId: AlertReceiveChannel['id'],
    datasource_uid: string,
    contact_point_name: string
  ) {
    return await makeRequest(`${this.path}${alertReceiveChannelId}/connect_contact_point`, {
      method: 'POST',
      data: {
        datasource_uid,
        contact_point_name,
      },
    });
  }

  async disconnectContactPoint(
    alertReceiveChannelId: AlertReceiveChannel['id'],
    datasource_uid: string,
    contact_point_name: string
  ) {
    return await makeRequest(`${this.path}${alertReceiveChannelId}/disconnect_contact_point`, {
      method: 'POST',
      data: {
        datasource_uid,
        contact_point_name,
      },
    });
  }

  async createContactPoint(
    alertReceiveChannelId: AlertReceiveChannel['id'],
    datasource_uid: string,
    contact_point_name: string
  ) {
    return await makeRequest(`${this.path}${alertReceiveChannelId}/create_contact_point`, {
      method: 'POST',
      data: {
        datasource_uid,
        contact_point_name,
      },
    });
  }

  async getAccessLogs(alertReceiveChannelId: AlertReceiveChannel['id']) {
    const { integration_log } = await makeRequest(`/alert_receive_channel_access_log/${alertReceiveChannelId}/`, {});

    return integration_log;
  }

  async installSentry(sentry_payload: string) {
    return await makeRequest('/sentry_complete_install/', {
      method: 'POST',
      params: { sentry_payload },
    });
  }

  async sendDemoAlert(id: AlertReceiveChannel['id'], payload: string = undefined) {
    const requestConfig: any = {
      method: 'POST',
    };

    if (payload) {
      requestConfig.data = {
        demo_alert_payload: payload,
      };
    }

    await makeRequest(`${this.path}${id}/send_demo_alert/`, requestConfig).catch(showApiError);

    Mixpanel.track('Send Demo Incident', null);
  }

  async sendDemoAlertToParticularRoute(id: ChannelFilter['id']) {
    await makeRequest(`/channel_filters/${id}/send_demo_alert/`, { method: 'POST' }).catch(showApiError);
  }

  async convertRegexpTemplateToJinja2Template(id: ChannelFilter['id']) {
    const result = await makeRequest(`/channel_filters/${id}/convert_from_regex_to_jinja2/`, { method: 'POST' }).catch(
      showApiError
    );
    return result;
  }

  async renderPreview(id: AlertReceiveChannel['id'], template_name: string, template_body: string, payload: JSON) {
    return await makeRequest(`${this.path}${id}/preview_template/`, {
      method: 'POST',
      data: { template_name, template_body, payload },
    });
  }

  async changeTeam(id: AlertReceiveChannel['id'], teamId: GrafanaTeam['id']) {
    return await makeRequest(`${this.path}${id}/change_team`, {
      params: { team_id: String(teamId) },
      method: 'PUT',
    });
  }

  async updateCounters() {
    const counters = await makeRequest(`${this.path}counters`, {
      method: 'GET',
    });

    this.counters = counters;
  }

  startMaintenanceMode = (id: AlertReceiveChannel['id'], mode: MaintenanceMode, duration: number): Promise<void> =>
    makeRequest<null>(`${this.path}${id}/start_maintenance/`, {
      method: 'POST',
      data: {
        mode,
        duration,
      },
    });

  stopMaintenanceMode = (id: AlertReceiveChannel['id']) =>
    makeRequest<null>(`${this.path}${id}/stop_maintenance/`, {
      method: 'POST',
    });
}
