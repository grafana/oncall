import { action, observable } from 'mobx';

import { ActionDTO } from 'models/action';
import { AlertTemplatesDTO } from 'models/alert_templates';
import { Alert } from 'models/alertgroup/alertgroup.types';
import BaseStore from 'models/base_store';
import { ChannelFilter } from 'models/channel_filter/channel_filter.types';
import { Heartbeat } from 'models/heartbeat/heartbeat.types';
import { OutgoingWebhook } from 'models/outgoing_webhook/outgoing_webhook.types';
import { TemplatePreview } from 'models/types';
import { RequestConfig, makeRequest } from 'network';
import { Mixpanel } from 'services/mixpanel';
import { RootStore } from 'state';
import { move } from 'state/helpers';
import { SelectOption } from 'state/types';
import { showApiError } from 'utils';
import { PageNumberPaginatedApiResponse } from 'utils/pagination/types';

import {
  AlertReceiveChannel,
  AlertReceiveChannelOption,
  AlertReceiveChannelCounters,
  MaintenanceMode,
} from './alert_receive_channel.types';

type AlertReceiveChannelId = AlertReceiveChannel['id'];
type AlertGroupId = Alert['pk'];
type HeartbeatId = Heartbeat['id'];
type ChannelFilterId = ChannelFilter['id'];
type CustomButtonId = ActionDTO['id'];

type AlertReceiveChannels = AlertReceiveChannel[];
type AlertReceiveChannelOptions = AlertReceiveChannelOption[];
type AlertTemplatesDTOs = AlertTemplatesDTO[];
type OutgoingWebhooks = OutgoingWebhook[];

type AlertReceiveChannelPayload = Partial<AlertReceiveChannel>;
type ChannelFilterRequestPayload = Partial<ChannelFilter>;

export type AlertReceiveChannelIdToObjectMap = Record<AlertReceiveChannelId, AlertReceiveChannel>;
type AlertReceiveChannelIdToAlertReceiveChannelCountersMap = Record<AlertReceiveChannelId, AlertReceiveChannelCounters>;
type AlertReceiveChannelIdToHeartbeatIdMap = Record<AlertReceiveChannelId, HeartbeatId>;
type AlertReceiveChannelIdToChannelFilterIdsMap = Record<AlertReceiveChannelId, ChannelFilterId[]>;
type AlertReceiveChannelIdToAlertTemplatesMap = Record<AlertReceiveChannelId, AlertTemplatesDTOs>;
type AlertReceiveChannelIdToOutgoingWebhookMap = Record<AlertGroupId, OutgoingWebhooks>;
type ChannelFilterIdToChannelFilterMap = Record<ChannelFilterId, ChannelFilter>;

type PaginatedAPIResponse = PageNumberPaginatedApiResponse<AlertReceiveChannel>;

export class AlertReceiveChannelStore extends BaseStore {
  @observable.shallow
  searchResult: AlertReceiveChannelId[];

  @observable.shallow
  paginatedSearchResult: PageNumberPaginatedApiResponse<AlertReceiveChannelId> = null;

  @observable.shallow
  items: AlertReceiveChannelIdToObjectMap = {};

  @observable.shallow
  counters: AlertReceiveChannelIdToAlertReceiveChannelCountersMap = {};

  @observable
  channelFilterIds: AlertReceiveChannelIdToChannelFilterIdsMap = {};

  @observable.shallow
  channelFilters: ChannelFilterIdToChannelFilterMap = {};

  @observable
  alertReceiveChannelToHeartbeat: AlertReceiveChannelIdToHeartbeatIdMap = {};

  @observable.shallow
  actions: AlertReceiveChannelIdToOutgoingWebhookMap = {};

  @observable.shallow
  alertReceiveChannelOptions: AlertReceiveChannelOptions = [];

  @observable.shallow
  templates: AlertReceiveChannelIdToAlertTemplatesMap = {};

  alertReceiveChannelTemplatesPath = '/alert_receive_channel_templates/';
  channelFiltersPath = '/channel_filters/';
  customButtonsPath = '/custom_buttons/';

  constructor(rootStore: RootStore) {
    super(rootStore);

    this.path = '/alert_receive_channels/';
  }

  getSearchResult(_query = ''): AlertReceiveChannels {
    if (!this.searchResult) {
      return undefined;
    }

    return this.searchResult.map((alertReceiveChannelId) => this.items[alertReceiveChannelId]);
  }

  getPaginatedSearchResult(_query = ''): PaginatedAPIResponse {
    const { paginatedSearchResult, items } = this;

    if (!paginatedSearchResult) {
      return undefined;
    }

    return {
      ...paginatedSearchResult,
      results: paginatedSearchResult.results.map((alertReceiveChannelId) => items[alertReceiveChannelId]),
    };
  }

  @action
  async loadItem(id: AlertReceiveChannelId, skipErrorHandling = false): Promise<AlertReceiveChannel | void> {
    const alertReceiveChannel = await this.getById<AlertReceiveChannel>(id, skipErrorHandling);

    if (!alertReceiveChannel) {
      return;
    }

    this.items = {
      ...this.items,
      [id]: alertReceiveChannel,
    };

    return alertReceiveChannel;
  }

  @action
  async updateItems(query: string | Record<string, any> = '', page = 1): Promise<PaginatedAPIResponse['results']> {
    const filters = typeof query === 'string' ? { search: query } : query;
    const { results, ...pagination } = await makeRequest<PaginatedAPIResponse>(this.path, {
      params: { ...filters, page },
    });

    const objectIds = results.map(({ id }) => id);

    this.items = {
      ...this.items,
      ...results.reduce(
        (acc, item) => ({
          ...acc,
          [item.id]: item,
        }),
        {} as AlertReceiveChannelIdToObjectMap
      ),
    };

    this.searchResult = objectIds;
    this.paginatedSearchResult = {
      ...pagination,
      results: objectIds,
    };

    this.rootStore.heartbeatStore.items = {
      ...this.rootStore.heartbeatStore.items,
      ...results.reduce((acc, { heartbeat }) => {
        if (heartbeat) {
          acc[heartbeat.id] = heartbeat;
        }

        return acc;
      }, {} as Record<HeartbeatId, Heartbeat>),
    };

    this.alertReceiveChannelToHeartbeat = {
      ...this.alertReceiveChannelToHeartbeat,
      ...results.reduce((acc, { id, heartbeat }) => {
        if (heartbeat) {
          acc[id] = heartbeat.id;
        }
        return acc;
      }, {} as AlertReceiveChannelIdToHeartbeatIdMap),
    };

    await this.updateCounters();

    return results;
  }

  @action
  async updateChannelFilters(alertReceiveChannelId: AlertReceiveChannelId, isOverwrite = false): Promise<void> {
    const response = await makeRequest<ChannelFilter[]>(this.channelFiltersPath, {
      params: { alert_receive_channel: alertReceiveChannelId },
    });

    const channelFilters = response.reduce(
      (acc, channelFilter) => ({
        ...acc,
        [channelFilter.id]: channelFilter,
      }),
      {} as ChannelFilterIdToChannelFilterMap
    );

    this.channelFilters = { ...this.channelFilters, ...channelFilters };

    if (isOverwrite) {
      // This is needed because on Move Up/Down/Removal the store no longer reflects the correct state
      this.channelFilters = channelFilters;
    }

    this.channelFilterIds = {
      ...this.channelFilterIds,
      [alertReceiveChannelId]: response.map(({ id }) => id),
    };
  }

  @action
  async updateChannelFilter(channelFilterId: ChannelFilterId): Promise<void> {
    const response = await makeRequest<ChannelFilter>(`${this.channelFiltersPath}${channelFilterId}/`);

    this.channelFilters = {
      ...this.channelFilters,
      [channelFilterId]: response,
    };
  }

  @action
  createChannelFilter = (data: ChannelFilterRequestPayload): Promise<ChannelFilter> =>
    makeRequest<ChannelFilter>(this.channelFiltersPath, { method: 'POST', data });

  @action
  async saveChannelFilter(channelFilterId: ChannelFilterId, data: ChannelFilterRequestPayload): Promise<ChannelFilter> {
    const response = await makeRequest<ChannelFilter>(`${this.channelFiltersPath}${channelFilterId}/`, {
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
    alertReceiveChannelId: AlertReceiveChannelId,
    oldIndex: number,
    newIndex: number
  ): Promise<void> {
    Mixpanel.track('Move ChannelFilter', null);

    const channelFilterId = this.channelFilterIds[alertReceiveChannelId][oldIndex];

    this.channelFilterIds[alertReceiveChannelId] = move(
      this.channelFilterIds[alertReceiveChannelId],
      oldIndex,
      newIndex
    );

    await makeRequest<ChannelFilter>(
      `${this.channelFiltersPath}${channelFilterId}/move_to_position/?position=${newIndex}`,
      {
        method: 'PUT',
      }
    );

    this.updateChannelFilters(alertReceiveChannelId, true);
  }

  @action
  async deleteChannelFilter(channelFilterId: ChannelFilterId): Promise<void> {
    Mixpanel.track('Delete ChannelFilter', null);

    const { alert_receive_channel: alertReceiveChannelId } = this.channelFilters[channelFilterId];

    this.channelFilterIds[alertReceiveChannelId].splice(
      this.channelFilterIds[alertReceiveChannelId].indexOf(channelFilterId),
      1
    );

    await makeRequest<null>(`${this.channelFiltersPath}${channelFilterId}`, {
      method: 'DELETE',
    });

    await this.updateChannelFilters(alertReceiveChannelId, true);
  }

  @action
  async updateAlertReceiveChannelOptions(): Promise<void> {
    const response = await makeRequest<AlertReceiveChannelOptions>(`${this.path}integration_options/`);
    this.alertReceiveChannelOptions = response;
  }

  getIntegration(alertReceiveChannel: AlertReceiveChannelPayload): AlertReceiveChannelOption | undefined {
    return this.alertReceiveChannelOptions.find(
      (alertReceiveChannelOption: SelectOption) => alertReceiveChannelOption.value === alertReceiveChannel.integration
    );
  }

  @action
  async saveAlertReceiveChannel(id: AlertReceiveChannelId, data: AlertReceiveChannelPayload) {
    const item = await this.update(id, data);

    this.items = {
      ...this.items,
      [id]: item,
    };
  }

  @action
  deleteAlertReceiveChannel(id: AlertReceiveChannelId): Promise<void> {
    return this.delete(id);
  }

  @action
  async updateTemplates(alertReceiveChannelId: AlertReceiveChannelId, alertGroupId?: AlertGroupId): Promise<void> {
    const response = await makeRequest<AlertTemplatesDTOs>(
      `${this.alertReceiveChannelTemplatesPath}${alertReceiveChannelId}/`,
      {
        params: { alert_group_id: alertGroupId },
        withCredentials: true,
      }
    );

    this.templates = {
      ...this.templates,
      [alertReceiveChannelId]: response,
    };
  }

  @action
  async updateItem(id: AlertReceiveChannelId): Promise<void> {
    const item = await this.getById<AlertReceiveChannel>(id);

    if (!item) {
      return;
    }

    this.items = {
      ...this.items,
      [id]: item,
    };
  }

  @action
  async saveTemplates(alertReceiveChannelId: AlertReceiveChannelId, data: Partial<AlertTemplatesDTO>): Promise<void> {
    const response = await makeRequest<AlertTemplatesDTOs>(
      `${this.alertReceiveChannelTemplatesPath}${alertReceiveChannelId}/`,
      {
        method: 'PUT',
        data,
        withCredentials: true,
      }
    );

    this.templates = {
      ...this.templates,
      [alertReceiveChannelId]: response,
    };
  }

  @action
  async updateCustomButtons(alertReceiveChannelId: AlertReceiveChannelId): Promise<void> {
    const response = await makeRequest<OutgoingWebhooks>(this.customButtonsPath, {
      params: {
        alert_receive_channel: alertReceiveChannelId,
      },
      withCredentials: true,
    });

    this.actions = {
      ...this.actions,
      [alertReceiveChannelId]: response,
    };
  }

  deleteCustomButton(id: CustomButtonId): Promise<void> {
    return makeRequest<null>(`${this.customButtonsPath}${id}/`, {
      method: 'DELETE',
      withCredentials: true,
    });
  }

  async sendDemoAlert(id: AlertReceiveChannelId, payload: string = undefined): Promise<void> {
    const requestConfig: RequestConfig = {
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

  async convertRegexpTemplateToJinja2Template(id: ChannelFilterId): Promise<ChannelFilter | void> {
    const result = await makeRequest<ChannelFilter>(`${this.channelFiltersPath}${id}/convert_from_regex_to_jinja2/`, {
      method: 'POST',
    }).catch(showApiError);
    return result;
  }

  renderPreview(
    id: AlertReceiveChannelId,
    template_name: string,
    template_body: string,
    payload: JSON
  ): Promise<TemplatePreview> {
    return makeRequest<TemplatePreview>(`${this.path}${id}/preview_template/`, {
      method: 'POST',
      data: { template_name, template_body, payload },
    });
  }

  async updateCounters(): Promise<void> {
    this.counters = await makeRequest<AlertReceiveChannelIdToAlertReceiveChannelCountersMap>(`${this.path}counters`, {
      method: 'GET',
    });
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
