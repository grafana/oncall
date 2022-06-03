import { action, observable } from 'mobx';

import BaseStore from 'models/base_store';
import { makeRequest } from 'network';
import { RootStore } from 'state';

import { CurlerCheck, CurlerCheckStats, CurlerCheckPing } from './curler.types';

export class CurlerStore extends BaseStore {
  @observable.shallow
  items: { [uuid: string]: CurlerCheck } = {};

  @observable.shallow
  searchResult: { [key: string]: Array<CurlerCheck['uuid']> } = {};

  @observable.shallow
  stats: { [uuid: string]: CurlerCheckStats } = {};

  @observable.shallow
  pings: {
    [uuid: string]: { [date: string]: CurlerCheckPing[] };
  } = {};

  constructor(rootStore: RootStore) {
    super(rootStore);

    this.path = '/curler/checks/';
  }

  @action
  async updateById(uuid: CurlerCheck['uuid']) {
    const response = await this.getById(uuid);

    this.items = {
      ...this.items,
      [uuid]: response,
    };
  }

  @action
  async updateItems(query = '', tzOffset: number) {
    const results = await makeRequest(`${this.path}`, {
      params: { search: query, offset: tzOffset },
    });

    this.items = {
      ...this.items,
      ...results.reduce(
        (acc: { [key: string]: CurlerCheck }, item: CurlerCheck) => ({
          ...acc,
          [item.uuid]: item,
        }),
        {}
      ),
    };

    this.searchResult = {
      ...this.searchResult,
      [query]: results.map((item: CurlerCheck) => item.uuid),
    };
  }

  getSearchResult(query = '') {
    if (!this.searchResult[query]) {
      return undefined;
    }

    return this.searchResult[query].map((checkId: CurlerCheck['uuid']) => this.items[checkId]);
  }

  @action
  async updateStats(uuid: CurlerCheck['uuid'], tzOffset: number) {
    const response = await makeRequest(`${this.path}${uuid}/stats/`, {
      params: { offset: tzOffset },
    });

    this.stats = {
      ...this.stats,
      [uuid]: response,
    };
  }

  @action
  async updatePings(uuid: CurlerCheck['uuid'], date: string, tzOffset: number) {
    const response = await makeRequest(`${this.path}${uuid}/pings/`, {
      params: { created_at__date: date, offset: tzOffset },
    });

    this.pings = {
      ...this.pings,
      [uuid]: {
        ...this.pings[uuid],
        [date]: response,
      },
    };
  }

  @action
  async pause(uuid: CurlerCheck['uuid']) {
    return await makeRequest(`${this.path}${uuid}/pause/`, {
      method: 'PUT',
    }).catch(this.onApiError);
  }

  @action
  async unpause(uuid: CurlerCheck['uuid']) {
    return await makeRequest(`${this.path}${uuid}/unpause/`, {
      method: 'PUT',
    }).catch(this.onApiError);
  }
}
