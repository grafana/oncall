import { action, observable, makeObservable, runInAction } from 'mobx';

import { BaseStore } from 'models/base_store';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
import { makeRequest } from 'network/network';
import { RootStore } from 'state/rootStore';

type TeamItems = { [id: string]: GrafanaTeam };

export class GrafanaTeamStore extends BaseStore {
  @observable
  searchResult: Array<GrafanaTeam['id']> = [];

  @observable.shallow
  items: TeamItems = {};

  constructor(rootStore: RootStore) {
    super(rootStore);

    makeObservable(this);

    this.path = '/teams/';
  }

  @action.bound
  async updateTeam(id: GrafanaTeam['id'], data: Partial<GrafanaTeam>) {
    const result = await this.update(id, data);

    runInAction(() => {
      this.items = {
        ...this.items,
        [id]: result,
      };
    });
  }

  @action.bound
  async updateItems(query = '', includeNoTeam = true, onlyIncludeNotifiableTeams = false, short = true) {
    const result = await makeRequest<GrafanaTeam[]>(`${this.path}`, {
      params: {
        search: query,
        short: short ? 'true' : 'false',
        include_no_team: includeNoTeam ? 'true' : 'false',
        only_include_notifiable_teams: onlyIncludeNotifiableTeams ? 'true' : 'false',
      },
    });

    runInAction(() => {
      this.items = {
        ...this.items,
        ...result.reduce<TeamItems>(
          (acc, item) => ({
            ...acc,
            [item.id]: item,
          }),
          {}
        ),
      };

      this.searchResult = result.map((item: GrafanaTeam) => item.id);
    });
  }

  @action.bound
  async fetchItemById(id: string) {
    const team = await this.getById(id);

    runInAction(() => {
      this.items = {
        ...this.items,
        [id]: team,
      };
    });
  }

  getSearchResult = () => {
    return this.searchResult.map((teamId: GrafanaTeam['id']) => this.items[teamId]);
  };
}
