import { action, computed, observable } from 'mobx';

import BaseStore from 'models/base_store';
import { makeRequest } from 'network';
import { RootStore } from 'state';

import { MSTeamsChannel } from './msteams_channel.types';

export class MSTeamsChannelStore extends BaseStore {
  @observable.shallow
  items: { [id: string]: MSTeamsChannel } = {};

  @observable
  currentTeamToMSTeamsChannel?: Array<MSTeamsChannel['id']>;

  @observable.shallow
  searchResult: { [key: string]: Array<MSTeamsChannel['id']> } = {};

  private autoUpdateTimer?: ReturnType<typeof setTimeout>;

  constructor(rootStore: RootStore) {
    super(rootStore);

    this.path = '/msteams/channels/';
  }

  @action
  async updateMSTeamsChannels() {
    const response = await makeRequest(this.path, {});

    const items = response.reduce(
      (acc: any, msteamsChannel: MSTeamsChannel) => ({
        ...acc,
        [msteamsChannel.id]: msteamsChannel,
      }),
      {}
    );

    this.items = {
      ...this.items,
      ...items,
    };

    this.currentTeamToMSTeamsChannel = response.map((msteamsChannel: MSTeamsChannel) => msteamsChannel.id);
  }

  @action
  async updateById(id: MSTeamsChannel['id']) {
    const response = await this.getById(id);

    this.items = {
      ...this.items,
      [id]: response,
    };
  }

  @action
  async updateItems(query = '') {
    const result = await this.getAll();

    this.items = {
      ...this.items,
      ...result.reduce(
        (acc: { [key: number]: MSTeamsChannel }, item: MSTeamsChannel) => ({
          ...acc,
          [item.id]: item,
        }),
        {}
      ),
    };

    this.searchResult = {
      ...this.searchResult,
      [query]: result.map((item: MSTeamsChannel) => item.id),
    };
  }

  getSearchResult(query = '') {
    if (!this.searchResult[query]) {
      return undefined;
    }
    return this.searchResult[query].map((msteamsChannelId: MSTeamsChannel['id']) => this.items[msteamsChannelId]);
  }

  @computed
  get hasItems() {
    return Boolean(this.getSearchResult('')?.length);
  }

  async startAutoUpdate() {
    this.autoUpdateTimer = setInterval(this.updateMSTeamsChannels.bind(this), 3000);
  }

  async stopAutoUpdate() {
    if (this.autoUpdateTimer) {
      clearInterval(this.autoUpdateTimer);
    }
  }

  async getMSTeamsChannelVerificationCode() {
    return await makeRequest(`/current_team/get_channel_verification_code/?backend=MSTEAMS`, {
      withCredentials: true,
    });
  }

  @action
  async makeMSTeamsChannelDefault(id: MSTeamsChannel['id']) {
    return makeRequest(`/msteams/channels/${id}/set_default/`, {
      method: 'POST',
    });
  }

  @action
  async deleteMSTeamsChannel(id: MSTeamsChannel['id']) {
    return super.delete(id);
  }

  async getMSTeamsChannels() {
    return super.getAll();
  }
}
