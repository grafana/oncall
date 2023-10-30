import { action, observable } from 'mobx';
import qs from 'query-string';

import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import BaseStore from 'models/base_store';
import { User } from 'models/user/user.types';
import { makeRequest } from 'network';
import { Mixpanel } from 'services/mixpanel';
import { RootStore } from 'state';
import { SelectOption } from 'state/types';
import { openErrorNotification, refreshPageError, showApiError } from 'utils';
import LocationHelper from 'utils/LocationHelper';

import { Alert, AlertAction, IncidentStatus } from './alertgroup.types';

export class AlertGroupStore extends BaseStore {
  @observable.shallow
  bulkActions: any = [];

  @observable.shallow
  silenceOptions: any;

  @observable.shallow
  items: { [id: string]: Alert } = {};

  @observable.shallow
  searchResult: { [key: string]: Array<Alert['pk']> } = {};

  @observable
  alertGroupsLoading = false;

  @observable
  needToParseFilters = false;

  @observable
  incidentFilters: any;

  initialQuery = qs.parse(window.location.search);

  @observable
  incidentsCursor?: string;

  @observable
  alertsSearchResult: {
    [key: string]: {
      prev?: string;
      next?: string;
      results?: string[];
      page_size?: number;
    };
  } = {};

  @observable
  alerts = new Map<string, Alert>();

  @observable
  newIncidents: any = {};

  @observable
  acknowledgedIncidents: any = {};

  @observable
  resolvedIncidents: any = {};

  @observable
  silencedIncidents: any = {};

  @observable
  alertGroupStats: any = {};

  @observable
  liveUpdatesEnabled = false;

  @observable
  liveUpdatesPaused = false;

  constructor(rootStore: RootStore) {
    super(rootStore);

    this.path = '/alertgroups/';
  }

  async attachAlert(pk: Alert['pk'], rootPk: Alert['pk']) {
    return await makeRequest(`${this.path}${pk}/attach/`, {
      method: 'POST',
      data: { root_alert_group_pk: rootPk },
    }).catch(showApiError);
  }

  async unattachAlert(pk: Alert['pk']) {
    return await makeRequest(`${this.path}${pk}/unattach/`, {
      method: 'POST',
    }).catch(showApiError);
  }

  async updateItem(id: Alert['pk']) {
    const item = await this.getById(id);

    this.items = {
      ...this.items,
      [item.id]: item,
    };
  }

  getSearchResult(query = '') {
    if (!this.searchResult[query]) {
      return undefined;
    }

    return this.searchResult[query].map((id: Alert['pk']) => this.items[id]);
  }

  async getAlertGroupsForIntegration(integrationId: AlertReceiveChannel['id']) {
    const { results } = await makeRequest(`${this.path}`, {
      params: { integration: integrationId },
    });
    return results;
  }

  async getAlertsFromGroup(pk: Alert['pk']) {
    return await makeRequest(`${this.path}${pk}`, {});
  }

  @action
  async updateSilenceOptions() {
    this.silenceOptions = await makeRequest(`${this.path}silence_options/`, {});
  }

  @action
  async resolve(id: Alert['pk'], delay: number) {
    await makeRequest(`${this.path}${id}/silence/`, {
      method: 'POST',
      data: { delay },
    });
  }

  @action
  async unresolve(id: Alert['pk']) {
    await makeRequest(`${this.path}${id}/unresolve/`, {
      method: 'POST',
    });
  }

  @action
  async acknowledge(id: Alert['pk']) {
    await makeRequest(`${this.path}${id}/acknowledge/`, {
      method: 'POST',
    });
  }

  @action
  async unacknowledge(id: Alert['pk']) {
    await makeRequest(`${this.path}${id}/unacknowledge/`, {
      method: 'POST',
    });
  }

  @action
  async silence(id: Alert['pk'], delay: number) {
    await makeRequest(`${this.path}${id}/silence/`, {
      method: 'POST',
      data: { delay },
    });
  }

  @action
  async unsilence(id: Alert['pk']) {
    await makeRequest(`${this.path}${id}/unsilence/`, {
      method: 'POST',
    });
  }

  @action
  async updateBulkActions() {
    const response = await makeRequest(`${this.path}bulk_action_options/`, {});

    this.bulkActions = response.reduce(
      (acc: { [key: string]: boolean }, item: SelectOption) => ({
        ...acc,
        [item.value]: true,
      }),
      {}
    );
  }

  async bulkAction(data: any) {
    return await makeRequest(`${this.path}bulk_action/`, {
      method: 'POST',
      data,
    });
  }

  async renderPreview(id: Alert['pk'], template_name: string, template_body: string) {
    return await makeRequest(`${this.path}${id}/preview_template/`, {
      method: 'POST',
      data: { template_name, template_body },
    });
  }

  // methods were moved from rootBaseStore.
  // TODO check if methods are dublicating existing ones
  @action
  async updateIncidents() {
    await Promise.all([
      this.getNewIncidentsStats(),
      this.getAcknowledgedIncidentsStats(),
      this.getResolvedIncidentsStats(),
      this.getSilencedIncidentsStats(),
      this.updateAlertGroups(),
    ]);

    this.liveUpdatesPaused = false;
  }

  @action
  async updateIncidentFilters(params: any, keepCursor = false) {
    if (!keepCursor) {
      this.setIncidentsCursor(undefined);
    }

    this.incidentFilters = params;

    await this.updateIncidents();
  }

  @action
  async updateIncidentsCursor(cursor: string) {
    this.setIncidentsCursor(cursor);

    this.updateAlertGroups();
  }

  @action
  async setIncidentsCursor(cursor: string) {
    this.incidentsCursor = cursor;

    LocationHelper.update({ cursor }, 'partial');
  }

  @action
  async setIncidentsItemsPerPage() {
    this.setIncidentsCursor(undefined);

    this.updateAlertGroups();
  }

  @action
  async updateAlertGroups() {
    this.alertGroupsLoading = true;

    const {
      results,
      next: nextRaw,
      previous: previousRaw,
      page_size,
    } = await makeRequest(`${this.path}`, {
      params: {
        ...this.incidentFilters,
        perpage: this.alertsSearchResult?.['default']?.page_size,
        cursor: this.incidentsCursor,
        is_root: true,
      },
    }).catch(refreshPageError);

    const prevCursor = previousRaw ? qs.parse(qs.extract(previousRaw)).cursor : previousRaw;
    const nextCursor = nextRaw ? qs.parse(qs.extract(nextRaw)).cursor : nextRaw;

    const newAlerts = new Map(
      results.map((alert: Alert) => {
        const oldAlert = this.alerts.get(alert.pk) || {};
        const mergedAlertData = { ...oldAlert, ...alert };
        return [alert.pk, mergedAlertData];
      })
    );

    // @ts-ignore
    this.alerts = new Map<number, Alert>([...this.alerts, ...newAlerts]);

    this.alertsSearchResult['default'] = {
      prev: prevCursor,
      next: nextCursor,
      results: results.map((alert: Alert) => alert.pk),
      page_size,
    };

    this.alertGroupsLoading = false;
  }

  getAlertSearchResult(query: string) {
    const result = this.alertsSearchResult[query];
    if (!result) {
      return {};
    }

    return {
      prev: result.prev,
      next: result.next,
      page_size: result.page_size,
      results: result.results.map((pk: Alert['pk']) => this.alerts.get(pk)),
    };
  }

  @action
  async getAlert(pk: Alert['pk']) {
    return await makeRequest(`${this.path}${pk}`, {}).then((alert: Alert) => {
      this.alerts.set(pk, alert);

      return alert;
    });
  }

  async getPayloadForIncident(pk: Alert['pk']) {
    return await makeRequest(`/alerts/${pk}`, {});
  }

  @action
  async getNewIncidentsStats() {
    const result = await makeRequest(`${this.path}stats/`, {
      params: {
        ...this.incidentFilters,
        status: [IncidentStatus.Firing],
      },
    });
    this.newIncidents = result;
  }

  @action
  async getAcknowledgedIncidentsStats() {
    const result = await makeRequest(`${this.path}stats/`, {
      params: {
        ...this.incidentFilters,
        status: [IncidentStatus.Acknowledged],
      },
    });

    this.acknowledgedIncidents = result;
  }

  @action
  async getResolvedIncidentsStats() {
    const result = await makeRequest(`${this.path}stats/`, {
      params: {
        ...this.incidentFilters,
        status: [IncidentStatus.Resolved],
      },
    });

    this.resolvedIncidents = result;
  }

  @action
  async getSilencedIncidentsStats() {
    const result = await makeRequest(`${this.path}stats/`, {
      params: {
        ...this.incidentFilters,
        status: [IncidentStatus.Silenced],
      },
    });

    this.silencedIncidents = result;
  }

  @action
  async getAlertGroupsStats() {
    this.alertGroupStats = await makeRequest('/alertgroups/stats/', {});
  }

  @action
  async doIncidentAction(alertId: Alert['pk'], action: AlertAction, isUndo = false, data?: any) {
    this.updateAlert(alertId, { loading: true });

    let undoAction = undefined;
    if (!isUndo) {
      switch (action) {
        case AlertAction.Acknowledge:
          Mixpanel.track('Acknowledge Incident', null);
          undoAction = AlertAction.unAcknowledge;
          break;
        case AlertAction.unAcknowledge:
          Mixpanel.track('Unacknowledge Incident', null);
          undoAction = AlertAction.Acknowledge;
          break;
        case AlertAction.Resolve:
          Mixpanel.track('Resolve Incident', null);
          undoAction = AlertAction.unResolve;
          break;
        case AlertAction.unResolve:
          Mixpanel.track('Unresolve Incident', null);
          undoAction = AlertAction.Resolve;
          break;
        case AlertAction.Silence:
          Mixpanel.track('Silence Incident', null);
          undoAction = AlertAction.unSilence;
          break;
        case AlertAction.unSilence:
          Mixpanel.track('Unsilence Incident', null);
          undoAction = AlertAction.Silence;
          break;
      }

      this.liveUpdatesPaused = true;
    }

    try {
      const result = await makeRequest(`/alertgroups/${alertId}/${action}/`, {
        method: 'POST',
        data,
      });

      this.updateAlert(alertId, {
        ...result,
        loading: false,
        undoAction,
      });
    } catch (e) {
      this.updateAlert(alertId, { loading: false });
      openErrorNotification(e.response.data?.detail || e.response.data);
    }
  }

  @action
  async updateAlert(pk: Alert['pk'], value: Partial<Alert>) {
    this.alerts.set(pk, {
      ...(this.alerts.get(pk) as Alert),
      ...value,
    });
  }

  @action
  toggleLiveUpdate(value: boolean) {
    this.liveUpdatesEnabled = value;
  }

  async unpageUser(alertId: Alert['pk'], userId: User['pk']) {
    return await makeRequest(`${this.path}${alertId}/unpage_user`, {
      method: 'POST',
      data: { user_id: userId },
    }).catch(this.onApiError);
  }
}
