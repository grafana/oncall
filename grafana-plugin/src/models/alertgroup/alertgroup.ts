import { action, observable } from 'mobx';
import qs from 'query-string';

import BaseStore from 'models/base_store';
import { makeRequest } from 'network';
import { Mixpanel } from 'services/mixpanel';
import { RootStore } from 'state';
import { SelectOption } from 'state/types';
import { showApiError } from 'utils';
import { openErrorNotification } from 'utils';

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
  incidentsPage: any = this.initialQuery.p ? Number(this.initialQuery.p) : 1;

  @observable
  alertsSearchResult: any = {};

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

  @action // FIXME for `attach to` feature ONLY
  async updateItems(query = '') {
    const { results } = await makeRequest(`${this.path}`, {
      params: { search: query, resolved: false, is_root: true },
    });

    this.items = {
      ...this.items,
      ...results.reduce(
        (acc: { [key: string]: Alert }, item: Alert) => ({
          ...acc,
          [item.pk]: item,
        }),
        {}
      ),
    };

    this.searchResult = {
      ...this.searchResult,
      [query]: results.map((item: Alert) => item.pk),
    };
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

  @action
  async updateSilenceOptions() {
    this.silenceOptions = await makeRequest(`${this.path}silence_options/`, {});
  }

  @action
  async resolve(id: Alert['pk'], delay: number) {
    const response = await makeRequest(`${this.path}${id}/silence/`, {
      method: 'POST',
      data: { delay },
    });
  }

  @action
  async unresolve(id: Alert['pk']) {
    const response = await makeRequest(`${this.path}${id}/unresolve/`, {
      method: 'POST',
    });
  }

  @action
  async acknowledge(id: Alert['pk']) {
    const response = await makeRequest(`${this.path}${id}/acknowledge/`, {
      method: 'POST',
    });
  }

  @action
  async unacknowledge(id: Alert['pk']) {
    const response = await makeRequest(`${this.path}${id}/unacknowledge/`, {
      method: 'POST',
    });
  }

  @action
  async silence(id: Alert['pk'], delay: number) {
    const response = await makeRequest(`${this.path}${id}/silence/`, {
      method: 'POST',
      data: { delay },
    });
  }

  @action
  async unsilence(id: Alert['pk']) {
    const response = await makeRequest(`${this.path}${id}/unsilence/`, {
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

  // methods were moved from rrotBaseStore.
  // TODO check if methods are dublicating existing ones
  @action
  async updateIncidents() {
    this.getNewIncidentsStats();
    this.getAcknowledgedIncidentsStats();
    this.getResolvedIncidentsStats();
    this.getSilencedIncidentsStats();

    this.updateAlertGroups();

    this.liveUpdatesPaused = false;
  }

  @action
  async updateIncidentFilters(params: any, resetPage = true) {
    if (resetPage) {
      this.incidentsPage = 1;
    }
    this.incidentFilters = params;

    this.updateIncidents();
  }

  @action
  async setIncidentsPage(page: number) {
    this.incidentsPage = page;

    this.updateAlertGroups();
  }

  @action
  async updateAlertGroups(skip_slow_rendering = true) {
    this.alertGroupsLoading = skip_slow_rendering;

    const result = await makeRequest(`${this.path}`, {
      params: {
        ...this.incidentFilters,
        page: this.incidentsPage,
        is_root: true,
        skip_slow_rendering,
      },
    });

    const newAlerts = new Map(result.results.map((alert: Alert) => [alert.pk, alert]));

    // @ts-ignore
    this.alerts = new Map<number, Alert>([...this.alerts, ...newAlerts]);

    this.alertsSearchResult['default'] = {
      count: result.count,
      results: result.results.map((alert: Alert) => alert.pk),
    };

    this.alertGroupsLoading = false;

    if (skip_slow_rendering) {
      const hasShortened = result.results.some((alert: Alert) => alert.short);

      if (hasShortened) {
        this.updateAlertGroups(false);
      }
    }
  }

  getAlertSearchResult(query: string) {
    if (!this.alertsSearchResult[query]) {
      return undefined;
    }

    return this.alertsSearchResult[query].results.map((pk: Alert['pk']) => this.alerts.get(pk));
  }

  @action
  async searchIncidents(search: string) {
    const result = await makeRequest(`${this.path}`, {
      params: {
        search,
        resolved: false,
        is_root: true,
      },
    });

    const newAlerts = new Map(result.results.map((alert: Alert) => [alert.pk, alert]));

    // @ts-ignore
    this.alerts = new Map<number, Alert>([...this.alerts, ...newAlerts]);

    this.alertsSearchResult[search] = {
      count: result.count,
      results: result.results.map((alert: Alert) => alert.pk),
    };
  }

  @action
  getAlert(pk: Alert['pk']) {
    return makeRequest(`${this.path}${pk}`, {}).then((alert: Alert) => {
      this.alerts.set(pk, alert);
    });
  }

  @action
  async getNewIncidentsStats() {
    const result = await makeRequest(`${this.path}stats/`, {
      params: {
        ...this.incidentFilters,
        resolved: false,
        acknowledged: false,
        status: [IncidentStatus.New],
      },
    });
    this.newIncidents = result;
  }

  @action
  async getAcknowledgedIncidentsStats() {
    const result = await makeRequest(`${this.path}stats/`, {
      params: {
        ...this.incidentFilters,
        resolved: false,
        acknowledged: true,
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
        resolved: true,
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
        silenced: true,
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

    console.log('action', action);
    console.log('isUndo', isUndo);

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

      console.log('undoAction', undoAction);
    } catch (e) {
      this.updateAlert(alertId, { loading: false });

      openErrorNotification(e.response.data?.detail);
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
}
