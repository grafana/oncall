import { action, observable, makeObservable, runInAction } from 'mobx';

import { BaseStore } from 'models/base_store';
import { makeRequest } from 'network/network';
import { RootStore } from 'state/rootStore';

import { ZoomChannel } from './zoom.types';

export class ZoomChannelStore extends BaseStore {
  @observable.shallow
  items: { [id: string]: ZoomChannel } = {};

  @observable.shallow
  searchResult: { [key: string]: Array<ZoomChannel['id']> } = {};

  constructor(rootStore: RootStore) {
    super(rootStore);

    makeObservable(this);

    this.path = '/zoom_channels/';
  }

  @action.bound
  async updateZoomChannels() {
    const response = await makeRequest<ZoomChannel[]>(this.path, {});

    const items = response.reduce(
      (acc: any, zoomChannel: ZoomChannel) => ({
        ...acc,
        [zoomChannel.id]: zoomChannel,
      }),
      {}
    );

    runInAction(() => {
      this.items = {
        ...this.items,
        ...items,
      };
    });
  }

  @action.bound
  async updateById(id: ZoomChannel['id']) {
    const response = await this.getById(id);

    runInAction(() => {
      this.items = {
        ...this.items,
        [id]: response,
      };
    });
  }

  @action.bound
  async updateItems(query = '') {
    const result = await this.getAll();

    runInAction(() => {
      this.items = {
        ...this.items,
        ...result.reduce(
          (acc: { [key: number]: ZoomChannel }, item: ZoomChannel) => ({
            ...acc,
            [item.id]: item,
          }),
          {}
        ),
      };

      this.searchResult = {
        ...this.searchResult,
        [query]: result.map((item: ZoomChannel) => item.id),
      };
    });
  }

  getSearchResult = (query = '') => {
    if (!this.searchResult[query]) {
      return undefined;
    }
    return this.searchResult[query].map((zoomChannelId: ZoomChannel['id']) => this.items[zoomChannelId]);
  };

  @action.bound
  async makeZoomChannelDefault(id: ZoomChannel['id']) {
    return makeRequest(`/zoom_channels/${id}/set_default/`, {
      method: 'POST',
    });
  }

  async deleteZoomChannel(id: ZoomChannel['id']) {
    return super.delete(id);
  }
}
