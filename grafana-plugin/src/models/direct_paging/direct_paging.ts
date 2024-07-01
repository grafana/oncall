import { action, observable, makeObservable } from 'mobx';

import { UserResponders } from 'containers/AddResponders/AddResponders.types';
import { BaseStore } from 'models/base_store';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
import { makeRequest } from 'network/network';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { RootStore } from 'state/rootStore';

import { ManualAlertGroupPayload } from './direct_paging.types';

type DirectPagingResponse = {
  alert_group_id: string;
};

export class DirectPagingStore extends BaseStore {
  @observable
  selectedTeamResponder: GrafanaTeam | null = null;

  @observable
  selectedUserResponders: UserResponders = [];

  constructor(rootStore: RootStore) {
    super(rootStore);

    makeObservable(this);

    this.path = '/direct_paging/';
  }

  @action.bound
  addUserToSelectedUsers = (user: ApiSchemas['UserIsCurrentlyOnCall']) => {
    this.selectedUserResponders = [
      ...this.selectedUserResponders,
      {
        data: user,
        important: false,
      },
    ];
  };

  @action.bound
  resetSelectedUsers = () => {
    this.selectedUserResponders = [];
  };

  @action.bound
  updateSelectedTeam = (team: GrafanaTeam) => {
    this.selectedTeamResponder = team;
  };

  @action.bound
  resetSelectedTeam = () => {
    this.selectedTeamResponder = null;
  };

  @action.bound
  removeSelectedUser(index: number) {
    this.selectedUserResponders = [
      ...this.selectedUserResponders.slice(0, index),
      ...this.selectedUserResponders.slice(index + 1),
    ];
  }

  @action.bound
  updateSelectedUserImportantStatus(index: number, important: boolean) {
    this.selectedUserResponders = [
      ...this.selectedUserResponders.slice(0, index),
      {
        ...this.selectedUserResponders[index],
        important,
      },
      ...this.selectedUserResponders.slice(index + 1),
    ];
  }

  async createManualAlertRule(data: ManualAlertGroupPayload): Promise<DirectPagingResponse | void> {
    try {
      return await makeRequest<DirectPagingResponse>(this.path, {
        method: 'POST',
        data,
      });
    } catch (err) {
      this.onApiError(err);
    }
  }

  async updateAlertGroup(
    alertId: ApiSchemas['AlertGroup']['pk'],
    data: ManualAlertGroupPayload
  ): Promise<DirectPagingResponse | void> {
    try {
      return await makeRequest<DirectPagingResponse>(this.path, {
        method: 'POST',
        data: {
          alert_group_id: alertId,
          ...data,
        },
      });
    } catch (err) {
      this.onApiError(err);
    }
  }
}
