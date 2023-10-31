import { action, observable } from 'mobx';

import { UserResponders } from 'containers/AddResponders/AddResponders.types';
import { Alert } from 'models/alertgroup/alertgroup.types';
import BaseStore from 'models/base_store';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
import { User } from 'models/user/user.types';
import { makeRequest } from 'network';
import { RootStore } from 'state';

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

    this.path = '/direct_paging/';
  }

  @action
  addUserToSelectedUsers = (user: User) => {
    this.selectedUserResponders = [
      ...this.selectedUserResponders,
      {
        data: user,
        important: false,
      },
    ];
  };

  @action
  resetSelectedUsers = () => {
    this.selectedUserResponders = [];
  };

  @action
  updateSelectedTeam = (team: GrafanaTeam) => {
    this.selectedTeamResponder = team;
  };

  @action
  resetSelectedTeam = () => {
    this.selectedTeamResponder = null;
  };

  @action
  removeSelectedUser(index: number) {
    this.selectedUserResponders = [
      ...this.selectedUserResponders.slice(0, index),
      ...this.selectedUserResponders.slice(index + 1),
    ];
  }

  @action
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
    return await makeRequest<DirectPagingResponse>(this.path, {
      method: 'POST',
      data,
    }).catch(this.onApiError);
  }

  async updateAlertGroup(alertId: Alert['pk'], data: ManualAlertGroupPayload): Promise<DirectPagingResponse | void> {
    return await makeRequest<DirectPagingResponse>(this.path, {
      method: 'POST',
      data: {
        alert_group_id: alertId,
        ...data,
      },
    }).catch(this.onApiError);
  }
}
