import { action, computed, observable } from 'mobx';

import BaseStore from 'models/base_store';
import { makeRequest } from 'network';
import { RootStore } from 'state';

import { TelegramChannel } from './telegram_channel.types';

export class TelegramChannelStore extends BaseStore {
  @observable.shallow
  items: { [id: string]: TelegramChannel } = {};

  @observable
  currentTeamToTelegramChannel?: Array<TelegramChannel['id']>;

  @observable.shallow
  searchResult: { [key: string]: Array<TelegramChannel['id']> } = {};

  private autoUpdateTimer?: ReturnType<typeof setTimeout>;

  constructor(rootStore: RootStore) {
    super(rootStore);

    this.path = '/telegram_channels/';
  }

  @action
  async updateTelegramChannels() {
    const response = await makeRequest(this.path, {});

    const items = response.reduce(
      (acc: any, telegramChannel: TelegramChannel) => ({
        ...acc,
        [telegramChannel.id]: telegramChannel,
      }),
      {}
    );

    this.items = {
      ...this.items,
      ...items,
    };

    this.currentTeamToTelegramChannel = response.map((telegramChannel: TelegramChannel) => telegramChannel.id);
  }

  @action
  async updateById(id: TelegramChannel['id']) {
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
        (acc: { [key: number]: TelegramChannel }, item: TelegramChannel) => ({
          ...acc,
          [item.id]: item,
        }),
        {}
      ),
    };

    this.searchResult = {
      ...this.searchResult,
      [query]: result.map((item: TelegramChannel) => item.id),
    };
  }

  getSearchResult(query = '') {
    if (!this.searchResult[query]) {
      return undefined;
    }
    return this.searchResult[query].map((telegramChannelId: TelegramChannel['id']) => this.items[telegramChannelId]);
  }

  @computed
  get hasItems() {
    return Boolean(this.getSearchResult('')?.length);
  }

  async startAutoUpdate() {
    this.autoUpdateTimer = setInterval(this.updateTelegramChannels.bind(this), 3000);
  }

  async stopAutoUpdate() {
    if (this.autoUpdateTimer) {
      clearInterval(this.autoUpdateTimer);
    }
  }

  async getTelegramVerificationCode() {
    return await makeRequest(`/current_team/get_telegram_verification_code/`, {
      withCredentials: true,
    });
  }

  @action
  async makeTelegramChannelDefault(id: TelegramChannel['id']) {
    return makeRequest(`/telegram_channels/${id}/set_default/`, {
      method: 'POST',
    });
  }

  @action
  async deleteTelegramChannel(id: TelegramChannel['id']) {
    return super.delete(id);
  }

  async getTelegramChannels() {
    return super.getAll();
  }
}
