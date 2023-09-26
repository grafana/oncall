import { action, observable } from 'mobx';

import BaseStore from 'models/base_store';
import { makeRequest } from 'network';
import { RootStore } from 'state';

import { Key, Value } from './label.types';

export class LabelStore extends BaseStore {
  @observable.shallow
  public keys: Key[] = [];

  @observable.shallow
  public values: { [key: string]: Value[] } = {};

  constructor(rootStore: RootStore) {
    super(rootStore);

    this.path = '/labels/';

    this.updateKeys();
  }

  @action
  public async updateKeys() {
    const result = await makeRequest(`${this.path}keys`, {
      params: {},
    });

    this.keys = result;

    return result;
  }

  @action
  public async getValuesForKey(keyId: string) {
    const result = await makeRequest(`${this.path}${keyId}`, {
      params: {},
    });

    this.values = {
      ...this.values,
      [keyId]: result.values,
    };

    return result;
  }

  public async createKey(key: string) {
    const result = await makeRequest(`${this.path}`, {
      method: 'POST',
      data: { key: { repr: key }, values: [] },
    });

    console.log('create key', key, result);

    return result;
  }

  public async addValue(keyId: Key['id'], value: string) {
    const result = await makeRequest(`${this.path}${keyId}/value`, {
      method: 'POST',
      data: { repr: value },
    });

    console.log('addValue', keyId, value, result);

    return result;
  }
}
