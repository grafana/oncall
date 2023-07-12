import { action, observable } from 'mobx';

import BaseStore from 'models/base_store';
import { makeRequest } from 'network';
import { RootStore } from 'state';

import { Team } from './team.types';

export class TeamStore extends BaseStore {
  @observable
  redirectingToProperTeam = false;

  @observable.shallow
  teams: { [id: number]: Team[] } = {};

  @observable
  currentTeam?: Team;

  constructor(rootStore: RootStore) {
    super(rootStore);

    this.path = '/team/';
  }

  @action
  async loadCurrentTeam() {
    this.currentTeam = await makeRequest('/current_team/', {});
  }

  @action
  async saveCurrentTeam(data: any) {
    this.currentTeam = await makeRequest('/current_team/', {
      method: 'PUT',
      data,
    });
  }
}
