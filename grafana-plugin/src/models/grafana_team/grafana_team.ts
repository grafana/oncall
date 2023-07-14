import { action, observable } from 'mobx';

import BaseStore from 'models/base_store';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
import { makeRequest } from 'network';
import { RootStore } from 'state';

export class GrafanaTeamStore extends BaseStore {
  @observable
  searchResult: { [key: string]: Array<GrafanaTeam['id']> } = {};

  @observable.shallow
  items: { [id: string]: GrafanaTeam } = {};

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
  async updateItems(query = '') {
    const result = await makeRequest(`${this.path}`, {
      params: { search: query },
    });

    this.items = {
      ...this.items,
      ...result.reduce(
        (acc: { [key: number]: GrafanaTeam }, item: GrafanaTeam) => ({
          ...acc,
          [item.id]: item,
        }),
        {}
      ),
    };

    this.searchResult = {
      ...this.searchResult,
      [query]: result.map((item: GrafanaTeam) => item.id),
    };
  }

  getSearchResult(query = '') {
    if (!this.searchResult[query]) {
      return undefined;
    }

    return this.searchResult[query].map((teamId: GrafanaTeam['id']) => this.items[teamId]);
  }
}
