import { action, observable } from 'mobx';

import BaseStore from 'models/base_store';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
import { makeRequest } from 'network';
import { RootStore } from 'state';

type TeamItems = { [id: string]: GrafanaTeam };

export class GrafanaTeamStore extends BaseStore {
  @observable
  searchResult: Array<GrafanaTeam['id']> = [];

  @observable.shallow
  items: TeamItems = {};

  constructor(rootStore: RootStore) {
    super(rootStore);

    this.path = '/teams/';
  }

  @action
  async updateTeam(id: GrafanaTeam['id'], data: Partial<GrafanaTeam>) {
    const result = await this.update(id, data);

    this.items = {
      ...this.items,
      [id]: result,
    };
  }

  @action
  async updateItems(query = '', includeNoTeam = true, onlyIncludeNotifiableTeams = false, short = true) {
    const result = await makeRequest<GrafanaTeam[]>(`${this.path}`, {
      params: {
        search: query,
        short: short ? 'true' : 'false',
        include_no_team: includeNoTeam ? 'true' : 'false',
        only_include_notifiable_teams: onlyIncludeNotifiableTeams ? 'true' : 'false',
      },
    });

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
  }

  getSearchResult() {
    return this.searchResult.map((teamId: GrafanaTeam['id']) => this.items[teamId]);
  }
}
