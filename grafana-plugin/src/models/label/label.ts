import { action, observable } from 'mobx';

import BaseStore from 'models/base_store';
import { makeRequest } from 'network';
import { RootStore } from 'state';

import { Label } from './label.types';

export class LabelStore extends BaseStore {
  @observable.shallow
  public items: { [id: number]: Label } = {};

  @observable.shallow
  public searchResult: { [key: string]: Array<Label['id']> } = {};

  constructor(rootStore: RootStore) {
    super(rootStore);

    this.path = '/labels/';
  }

  public async updateKeys() {
    const result = await makeRequest(`${this.path}keys`, {
      params: {},
    });

    console.log(result);

    return result;
  }

  public async createLabel(data: any) {
    const result = await makeRequest(`${this.path}`, {
      method: 'POST',
      params: {},
      data,
    });

    console.log(result);

    return result;
  }

  @action
  public async updateById(id: Label['id']) {
    const response = await this.getById(id);

    this.items = {
      ...this.items,
      [id]: response,
    };
  }

  @action
  public async updateItems(query = '') {
    const { results } = await makeRequest(`${this.path}`, {
      params: { search: query },
    });

    this.items = {
      ...this.items,
      ...results.reduce(
        (acc: { [key: number]: Label }, item: Label) => ({
          ...acc,
          [item.id]: item,
        }),
        {}
      ),
    };

    this.searchResult = {
      ...this.searchResult,
      [query]: results.map((item: Label) => item.id),
    };
  }

  getSearchResult(query = '') {
    if (!this.searchResult[query]) {
      return undefined;
    }

    return this.searchResult[query].map((labelId: Label['id']) => this.items[labelId]);
  }
}
