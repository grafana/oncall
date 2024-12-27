import { action, computed, observable, makeObservable, runInAction } from 'mobx';

import { BaseStore } from 'models/base_store';
import { makeRequest } from 'network/network';
import { RootStore } from 'state/rootStore';

import { MattermostChannel } from './mattermost.types';

export class MattermostChannelStore extends BaseStore {
  @observable.shallow
  items: { [id: string]: MattermostChannel } = {};

  @observable
  currentTeamToMattermostChannel?: Array<MattermostChannel['id']>;

  @observable.shallow
  searchResult: { [key: string]: Array<MattermostChannel['id']> } = {};

  private autoUpdateTimer?: ReturnType<typeof setTimeout>;

  constructor(rootStore: RootStore) {
    super(rootStore);

    makeObservable(this);

    this.path = '/mattermost/channels/';
  }

  @action.bound
  async updateMattermostChannels() {
    const response = await makeRequest(this.path, {});

    const items = response.reduce(
      (acc: any, mattermostChannel: MattermostChannel) => ({
        ...acc,
        [mattermostChannel.id]: mattermostChannel,
      }),
      {}
    );

    runInAction(() => {
      this.items = {
        ...this.items,
        ...items,
      };

      this.currentTeamToMattermostChannel = response.map((mattermostChannel: MattermostChannel) => mattermostChannel.id);
    });
  }

  @action.bound
  async updateById(id: MattermostChannel['id']) {
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
          (acc: { [key: number]: MattermostChannel }, item: MattermostChannel) => ({
            ...acc,
            [item.id]: item,
          }),
          {}
        ),
      };

      this.searchResult = {
        ...this.searchResult,
        [query]: result.map((item: MattermostChannel) => item.id),
      };
    });
  }

  getSearchResult = (query = '') => {
    if (!this.searchResult[query]) {
      return undefined;
    }
    return this.searchResult[query].map(
      (mattermostChannelId: MattermostChannel['id']) => this.items[mattermostChannelId]
    );
  };

  @computed
  get hasItems() {
    return Boolean(this.getSearchResult('')?.length);
  }

  async startAutoUpdate() {
    this.autoUpdateTimer = setInterval(this.updateMattermostChannels.bind(this), 3000);
  }

  async stopAutoUpdate() {
    if (this.autoUpdateTimer) {
      clearInterval(this.autoUpdateTimer);
    }
  }

  @action.bound
  async makeMattermostChannelDefault(id: MattermostChannel['id']) {
    return makeRequest(`/mattermost/channels/${id}/set_default`, {
      method: 'POST',
    });
  }

  async deleteMattermostChannel(id: MattermostChannel['id']) {
    return super.delete(id);
  }

  async getMattermostChannels() {
    return super.getAll();
  }
}
