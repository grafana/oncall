import { action, observable } from 'mobx';
import moment from 'moment-timezone';

import BaseStore from 'models/base_store';
import { makeRequest } from 'network';
import { RootStore } from 'state';

import { Webinar } from './webinar.types';

export class WebinarStore extends BaseStore {
  @observable.shallow
  searchResult?: { [key: string]: Array<Webinar['id']> };

  @observable.shallow
  items?: { [id: string]: Webinar };

  constructor(rootStore: RootStore) {
    super(rootStore);

    this.path = '/webinars/';
  }

  @action
  async subscribe(id: Webinar['id']) {
    return await makeRequest(`/webinars/${id}/subscribe/`, {
      method: 'POST',
      withCredentials: true,
    });
  }

  async updateItems(query = '') {
    const result = await this.getAll();

    this.items = {
      ...this.items,
      ...result.reduce(
        (acc: { [key: number]: Webinar }, item: Webinar) => ({
          ...acc,
          [item.id]: item,
        }),
        {}
      ),
    };

    this.searchResult = {
      ...(this.searchResult || {}),
      [query]: result.map((item: Webinar) => item.id),
    };
  }

  getSearchResult(query = '') {
    if (!this.searchResult || !this.items) {
      return undefined;
    }

    return this.searchResult[query].map((scheduleId: Webinar['id']) => this.items?.[scheduleId]);
  }

  getFutureWebinarsCount(): number {
    const items = this.getSearchResult();
    if (!items) {
      return 0;
    }

    return items.filter((webinar?: Webinar) => moment(webinar?.datetime).isAfter() && !webinar?.subscribed).length;
  }
}
