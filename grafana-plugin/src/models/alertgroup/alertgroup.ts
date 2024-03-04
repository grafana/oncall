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

import { AlertGroupHelper } from './alertgroup.helpers';
import { AlertGroupColumn, AlertAction, IncidentStatus } from './alertgroup.types';

export class AlertGroupStore {
  rootStore: RootStore;
  alerts = new Map<string, ApiSchemas['AlertGroup']>();
  bulkActions: any = [];
  silenceOptions: any;
  searchResult: { [key: string]: Array<ApiSchemas['AlertGroup']['pk']> } = {};
  incidentFilters: any;
  initialQuery = qs.parse(window.location.search);
  incidentsCursor?: string;
  alertsSearchResult: {
    prev?: string;
    next?: string;
    results?: string[];
    page_size?: number;
  } = {};
  stats: Record<IncidentStatus, number> | {} = {};
  liveUpdatesEnabled = false;
  liveUpdatesPaused = false;
  latestFetchAlertGroupsTimestamp: number;
  columns: AlertGroupColumn[] = [];
  isDefaultColumnOrder = false;

  constructor(rootStore: RootStore) {
    makeAutoObservable(this, undefined, { autoBind: true });
    this.rootStore = rootStore;
  }

  async fetchAlertGroups(isPollingJob = false, search?: string) {
    this.rootStore.loaderStore.setLoadingAction(
      isPollingJob ? ActionKey.FETCH_INCIDENTS_POLLING : ActionKey.FETCH_INCIDENTS,
      true
    );
    const timestamp = new Date().getTime();
    this.latestFetchAlertGroupsTimestamp = timestamp;
    const {
      data: { results, next: nextRaw, previous: previousRaw, page_size },
    } = await onCallApi().GET('/alertgroups/', {
      params: {
        query: {
          ...this.incidentFilters,
          search,
          perpage: this.alertsSearchResult?.page_size,
          cursor: this.incidentsCursor,
          is_root: true,
        },
      },
    });

    const prevCursor = previousRaw ? qs.parse(qs.extract(previousRaw)).cursor : previousRaw;
    const nextCursor = nextRaw ? qs.parse(qs.extract(nextRaw)).cursor : nextRaw;

    const newAlerts = new Map(
      results.map((alert: ApiSchemas['AlertGroup']) => {
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
      this.alerts = new Map<string, ApiSchemas['AlertGroup']>([...this.alerts, ...newAlerts]);

      this.alertsSearchResult = {
        prev: Array.isArray(prevCursor) ? prevCursor[0] : prevCursor,
        next: Array.isArray(nextCursor) ? nextCursor[0] : nextCursor,
        results: results.map((alert: ApiSchemas['AlertGroup']) => alert.pk),
        page_size,
      };
      this.rootStore.loaderStore.setLoadingAction(
        [ActionKey.FETCH_INCIDENTS, ActionKey.FETCH_INCIDENTS_POLLING],
        false
      );
    });
  }

  async getAlert(pk: ApiSchemas['AlertGroup']['pk']) {
    const { data: alertGroup } = await onCallApi().GET('/alertgroups/{id}/', {
      params: { path: { id: pk } },
    });
    runInAction(() => {
      this.alerts.set(pk, alertGroup);
    });
    this.rootStore.setPageTitle(`#${alertGroup.inside_organization_number} ${alertGroup.render_for_web.title}`);
  }

  async fetchIncidentsAndStats(isPollingJob = false) {
    await Promise.all([
      this.fetchStats(IncidentStatus.Firing),
      this.fetchStats(IncidentStatus.Acknowledged),
      this.fetchStats(IncidentStatus.Resolved),
      this.fetchStats(IncidentStatus.Silenced),
      this.fetchAlertGroups(isPollingJob),
    ]);
    this.setLiveUpdatesPaused(false);
  }

  async fetchSilenceOptions() {
    const { data } = await onCallApi().GET('/alertgroups/silence_options/', undefined);

    runInAction(() => {
      this.silenceOptions = data;
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

  async fetchBulkActions() {
    const { data } = await onCallApi().GET('/alertgroups/bulk_action_options/', undefined);

    runInAction(() => {
      this.bulkActions = data.reduce(
        (acc: { [key: string]: boolean }, item: SelectOption) => ({
          ...acc,
          [item.value]: true,
        }),
        {}
      );
    });
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

  async fetchStats(status: IncidentStatus) {
    const { data } = await onCallApi().GET('/alertgroups/stats/', {
      params: { query: { ...this.incidentFilters, status: [status] } },
    });

    runInAction(() => {
      this.stats[status] = data.count;
    });
  }

  async resolve(id: ApiSchemas['AlertGroup']['pk']) {
    this.setLiveUpdatesPaused(true);
    const { data } = await onCallApi().POST('/alertgroups/{id}/resolve/', {
      params: { path: { id } },
    });
    this.updateAlert(id, {
      ...data,
      undoAction: AlertAction.Resolve,
    });
  }

  async unresolve(id: ApiSchemas['AlertGroup']['pk']) {
    this.setLiveUpdatesPaused(true);
    const { data } = await onCallApi().POST('/alertgroups/{id}/unresolve/', { params: { path: { id } } });
    this.updateAlert(id, {
      ...data,
      undoAction: AlertAction.unResolve,
    });
  }

  async acknowledge(id: ApiSchemas['AlertGroup']['pk']) {
    this.setLiveUpdatesPaused(true);
    const { data } = await onCallApi().POST('/alertgroups/{id}/acknowledge/', { params: { path: { id } } });
    this.updateAlert(id, {
      ...data,
      undoAction: AlertAction.Acknowledge,
    });
  }

  async unacknowledge(id: ApiSchemas['AlertGroup']['pk']) {
    this.setLiveUpdatesPaused(true);
    const { data } = await onCallApi().POST('/alertgroups/{id}/unacknowledge/', { params: { path: { id } } });
    this.updateAlert(id, {
      ...data,
      undoAction: AlertAction.unAcknowledge,
    });
  }

  async silence(id: ApiSchemas['AlertGroup']['pk'], delay: number) {
    this.setLiveUpdatesPaused(true);
    const { data } = await onCallApi().POST('/alertgroups/{id}/silence/', {
      params: { path: { id } },
      body: { delay },
    });
    this.updateAlert(id, {
      ...data,
      undoAction: AlertAction.Silence,
    });
  }

  async unsilence(id: ApiSchemas['AlertGroup']['pk']) {
    this.setLiveUpdatesPaused(true);
    const { data } = await onCallApi().POST('/alertgroups/{id}/unsilence/', { params: { path: { id } } });
    this.updateAlert(id, {
      ...data,
      undoAction: AlertAction.unSilence,
    });
  }

  async doIncidentAction(id: ApiSchemas['AlertGroup']['pk'], action: AlertAction, delay?: number) {
    const actionToMethodMap = {
      [AlertAction.Acknowledge]: this.acknowledge,
      [AlertAction.unAcknowledge]: this.unacknowledge,
      [AlertAction.Silence]: this.silence,
      [AlertAction.unSilence]: this.unsilence,
      [AlertAction.Resolve]: this.resolve,
      [AlertAction.unResolve]: this.unresolve,
    };
    if (actionToMethodMap[action]) {
      await actionToMethodMap[action](id, delay);
    }
  }

  async updateAlert(pk: ApiSchemas['AlertGroup']['pk'], value: Partial<ApiSchemas['AlertGroup']>) {
    this.alerts.set(pk, {
      ...(this.alerts.get(pk) as ApiSchemas['AlertGroup']),
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
