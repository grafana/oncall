import { action, computed, observable } from 'mobx';

import BaseStore from 'models/base_store';
import { makeRequest } from 'network';
import { RootStore } from 'state';

import { DesktopChannel } from './desktop_channel.types';

export class DesktopChannelStore extends BaseStore {
  @observable.shallow
  items: { [id: string]: DesktopChannel } = {};

  @observable
  currentTeamToDesktopChannel?: Array<DesktopChannel['id']>;

  @observable.shallow
  searchResult: { [key: string]: Array<DesktopChannel['id']> } = {};

  private autoUpdateTimer?: ReturnType<typeof setTimeout>;

  constructor(rootStore: RootStore) {
    super(rootStore);

    this.path = '/dnotify/channels/';
  }

  @action
  async updateDesktopChannels() {
    const response = await makeRequest(this.path, {});

    const items = response.reduce(
      (acc: any, channel: DesktopChannel) => ({
        ...acc,
        [channel.id]: channel,
      }),
      {}
    );

    this.items = {
      ...this.items,
      ...items,
    };

    this.currentTeamToDesktopChannel = response.map((channel: DesktopChannel) => channel.id);
  }

  @action
  async updateById(id: DesktopChannel['id']) {
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
        (acc: { [key: number]: DesktopChannel }, item: DesktopChannel) => ({
          ...acc,
          [item.id]: item,
        }),
        {}
      ),
    };

    this.searchResult = {
      ...this.searchResult,
      [query]: result.map((item: DesktopChannel) => item.id),
    };
  }

  getSearchResult(query = '') {
    if (!this.searchResult[query]) {
      return undefined;
    }
    return this.searchResult[query].map((channelId: DesktopChannel['id']) => this.items[channelId]);
  }

  @computed
  get hasItems() {
    return Boolean(this.getSearchResult('')?.length);
  }

  async startAutoUpdate() {
    this.autoUpdateTimer = setInterval(this.updateDesktopChannels.bind(this), 3000);
  }

  async stopAutoUpdate() {
    if (this.autoUpdateTimer) {
      clearInterval(this.autoUpdateTimer);
    }
  }

  async getDesktopChannelVerificationCode() {
    return await makeRequest(`/current_team/get_channel_verification_code/?backend=DESKTOPDEMO`, {
      withCredentials: true,
    });
  }

  @action
  async makeDesktopChannelDefault(id: DesktopChannel['id']) {
    return makeRequest(`/dnotify/channels/${id}/set_default/`, {
      method: 'POST',
    });
  }

  @action
  async deleteDesktopChannel(id: DesktopChannel['id']) {
    return super.delete(id);
  }

  async getDesktopChannels() {
    return super.getAll();
  }
}
