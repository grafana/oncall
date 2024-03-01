import { runInAction, makeAutoObservable } from 'mobx';
import qs from 'query-string';

import { ActionKey } from 'models/loader/action-keys';
import { makeRequest } from 'network/network';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { onCallApi } from 'network/oncall-api/http-client';
import { RootStore } from 'state/rootStore';
import { SelectOption } from 'state/types';
import { LocationHelper } from 'utils/LocationHelper';
import { AutoLoadingState, WithGlobalNotification } from 'utils/decorators';
import { openErrorNotification, refreshPageError } from 'utils/utils';

import { AlertGroupHelper } from './alertgroup.helpers';
import { AlertGroupColumn, Alert, AlertAction, IncidentStatus } from './alertgroup.types';

export class AlertGroupStore {
  path = '/alertgroups/';
  rootStore: RootStore;
  bulkActions: any = [];
  silenceOptions: any;
  items: { [id: string]: ApiSchemas['AlertGroup'] } = {};
  searchResult: { [key: string]: Array<Alert['pk']> } = {};
  incidentFilters: any;
  initialQuery = qs.parse(window.location.search);
  incidentsCursor?: string;
  alertsSearchResult: {
    [key: string]: {
      prev?: string;
      next?: string;
      results?: string[];
      page_size?: number;
    };
  } = {};
  alerts = new Map<string, Alert>();
  newIncidents: any = {};
  acknowledgedIncidents: any = {};
  resolvedIncidents: any = {};
  silencedIncidents: any = {};
  liveUpdatesEnabled = false;
  liveUpdatesPaused = false;
  latestFetchAlertGroupsTimestamp: number;
  columns: AlertGroupColumn[] = [];
  isDefaultColumnOrder = false;

  constructor(rootStore: RootStore) {
    makeAutoObservable(this);
    this.rootStore = rootStore;
  }

  async fetchItemById(id: ApiSchemas['AlertGroup']['pk']) {
    const { data } = await onCallApi().GET('/alertgroups/{id}/', {
      params: { path: { id } },
    });

    runInAction(() => {
      this.items = {
        ...this.items,
        [data.pk]: data,
      };
    });
  }

  async fetchItems(query = '', params = {}) {
    const { results } = await makeRequest(`${this.path}`, {
      params: { search: query, ...params },
    });

    runInAction(() => {
      this.items = {
        ...this.items,
        ...results.reduce(
          (acc: { [key: number]: Alert }, item: Alert) => ({
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
    });
  }

  async fetchItemsAvailableForAttachment(query: string) {
    await this.fetchItems(query, {
      status: [IncidentStatus.Acknowledged, IncidentStatus.Firing, IncidentStatus.Silenced],
    });
  }

  async updateSilenceOptions() {
    const result = await makeRequest(`${this.path}silence_options/`, {});

    runInAction(() => {
      this.silenceOptions = result;
    });
  }

  @AutoLoadingState(ActionKey.RESET_COLUMNS_FROM_ALERT_GROUP)
  @WithGlobalNotification({ success: 'Columns list has been reset' })
  async resetColumns() {
    await AlertGroupHelper.resetTableSettings();
    await this.fetchTableSettings();
  }

  @AutoLoadingState(ActionKey.REMOVE_COLUMN_FROM_ALERT_GROUP)
  @WithGlobalNotification({
    success: 'Column has been removed from the list.',
    failure: 'There was an error processing your request. Please try again',
  })
  async removeTableColumn(
    columnToBeRemoved: AlertGroupColumn,
    convertColumnsToTableSettings: (columns: AlertGroupColumn[]) => {
      visible: AlertGroupColumn[];
      hidden: AlertGroupColumn[];
    }
  ) {
    const columns = this.columns.filter(
      (col) =>
        col.id !== columnToBeRemoved.id || (col.id === columnToBeRemoved.id && col.type !== columnToBeRemoved.type)
    );

    await this.updateTableSettings(convertColumnsToTableSettings(columns), false);
    await this.fetchTableSettings();
  }

  async updateBulkActions() {
    const response = await makeRequest(`${this.path}bulk_action_options/`, {});

    runInAction(() => {
      this.bulkActions = response.reduce(
        (acc: { [key: string]: boolean }, item: SelectOption) => ({
          ...acc,
          [item.value]: true,
        }),
        {}
      );
    });
  }

  async fetchIncidentsAndStats(isPollingJob = false) {
    await Promise.all([
      this.getNewIncidentsStats(),
      this.getAcknowledgedIncidentsStats(),
      this.getResolvedIncidentsStats(),
      this.getSilencedIncidentsStats(),
      this.fetchAlertGroups(isPollingJob),
    ]);
    this.setLiveUpdatesPaused(false);
  }

  setLiveUpdatesPaused(value: boolean) {
    this.liveUpdatesPaused = value;
  }

  @AutoLoadingState(ActionKey.UPDATE_FILTERS_AND_FETCH_INCIDENTS)
  async updateIncidentFiltersAndRefetchIncidentsAndStats(params: any, keepCursor = false) {
    if (!keepCursor) {
      this.setIncidentsCursor(undefined);
    }
    this.incidentFilters = params;
    await this.fetchIncidentsAndStats();
  }

  async updateIncidentsCursor(cursor: string) {
    this.setIncidentsCursor(cursor);

    this.fetchAlertGroups();
  }

  async setIncidentsCursor(cursor: string) {
    this.incidentsCursor = cursor;

    LocationHelper.update({ cursor }, 'partial');
  }

  async setIncidentsItemsPerPage() {
    this.setIncidentsCursor(undefined);

    this.fetchAlertGroups();
  }

  async fetchAlertGroups(isPollingJob = false) {
    this.rootStore.loaderStore.setLoadingAction(
      isPollingJob ? ActionKey.FETCH_INCIDENTS_POLLING : ActionKey.FETCH_INCIDENTS,
      true
    );
    const timestamp = new Date().getTime();
    this.latestFetchAlertGroupsTimestamp = timestamp;
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
        const mergedAlertData = { ...oldAlert, ...alert, undoAction: alert.undoAction };
        return [alert.pk, mergedAlertData];
      })
    );

    runInAction(() => {
      // If previous fetch took longer than the next one, we ignore result of the previous fetch
      if (timestamp !== this.latestFetchAlertGroupsTimestamp) {
        return;
      }
      // @ts-ignore
      this.alerts = new Map<number, Alert>([...this.alerts, ...newAlerts]);

      this.alertsSearchResult['default'] = {
        prev: prevCursor,
        next: nextCursor,
        results: results.map((alert: Alert) => alert.pk),
        page_size,
      };
      this.rootStore.loaderStore.setLoadingAction(
        [ActionKey.FETCH_INCIDENTS, ActionKey.FETCH_INCIDENTS_POLLING],
        false
      );
    });
  }

  async getAlert(pk: Alert['pk']) {
    const alertGroup = await makeRequest(`${this.path}${pk}`, {});
    runInAction(() => {
      this.alerts.set(pk, alertGroup);
    });
    this.rootStore.setPageTitle(`#${alertGroup.inside_organization_number} ${alertGroup.render_for_web.title}`);
  }

  async getNewIncidentsStats() {
    const result = await makeRequest(`${this.path}stats/`, {
      params: {
        ...this.incidentFilters,
        status: [IncidentStatus.Firing],
      },
    });

    runInAction(() => {
      this.newIncidents = result;
    });
  }

  async getAcknowledgedIncidentsStats() {
    const result = await makeRequest(`${this.path}stats/`, {
      params: {
        ...this.incidentFilters,
        status: [IncidentStatus.Acknowledged],
      },
    });

    runInAction(() => {
      this.acknowledgedIncidents = result;
    });
  }

  async getResolvedIncidentsStats() {
    const result = await makeRequest(`${this.path}stats/`, {
      params: {
        ...this.incidentFilters,
        status: [IncidentStatus.Resolved],
      },
    });

    runInAction(() => {
      this.resolvedIncidents = result;
    });
  }

  async getSilencedIncidentsStats() {
    const result = await makeRequest(`${this.path}stats/`, {
      params: {
        ...this.incidentFilters,
        status: [IncidentStatus.Silenced],
      },
    });

    runInAction(() => {
      this.silencedIncidents = result;
    });
  }

  async doIncidentAction(alertId: Alert['pk'], action: AlertAction, isUndo = false, data?: any) {
    this.updateAlert(alertId, { loading: true });

    let undoAction = undefined;
    if (!isUndo) {
      switch (action) {
        case AlertAction.Acknowledge:
          undoAction = AlertAction.unAcknowledge;
          break;
        case AlertAction.unAcknowledge:
          undoAction = AlertAction.Acknowledge;
          break;
        case AlertAction.Resolve:
          undoAction = AlertAction.unResolve;
          break;
        case AlertAction.unResolve:
          undoAction = AlertAction.Resolve;
          break;
        case AlertAction.Silence:
          undoAction = AlertAction.unSilence;
          break;
        case AlertAction.unSilence:
          undoAction = AlertAction.Silence;
          break;
      }

      this.setLiveUpdatesPaused(true);
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

  async updateAlert(pk: Alert['pk'], value: Partial<Alert>) {
    this.alerts.set(pk, {
      ...(this.alerts.get(pk) as Alert),
      ...value,
    });
  }

  async fetchTableSettings(): Promise<void> {
    const tableSettings = await makeRequest('/alertgroup_table_settings', {});

    const { hidden, visible, default: isDefaultOrder } = tableSettings;

    runInAction(() => {
      this.isDefaultColumnOrder = isDefaultOrder;
      this.columns = [
        ...visible.map((item: AlertGroupColumn): AlertGroupColumn => ({ ...item, isVisible: true })),
        ...hidden.map((item: AlertGroupColumn): AlertGroupColumn => ({ ...item, isVisible: false })),
      ];
    });
  }

  @AutoLoadingState(ActionKey.ADD_NEW_COLUMN_TO_ALERT_GROUP)
  async updateTableSettings(
    columns: { visible: AlertGroupColumn[]; hidden: AlertGroupColumn[] },
    isUserUpdate: boolean
  ): Promise<void> {
    const method = isUserUpdate ? 'PUT' : 'POST';

    const { default: isDefaultOrder } = await makeRequest('/alertgroup_table_settings', {
      method,
      data: { ...columns },
    });

    runInAction(() => {
      this.isDefaultColumnOrder = isDefaultOrder;
    });
  }
}
