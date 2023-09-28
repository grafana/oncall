import { action, observable, toJS } from 'mobx';

import BaseStore from 'models/base_store';
import { makeRequest } from 'network';
import { RootStore } from 'state';

import { LabelKey, LabelValue } from './label.types';

export class LabelStore extends BaseStore {
  @observable.shallow
  public keys: LabelKey[] = [];

  @observable.shallow
  public values: { [key: string]: LabelValue[] } = {};

  constructor(rootStore: RootStore) {
    super(rootStore);

    this.path = '/labels/';

    this.updateKeys();
  }

  @action
  public async updateKeys() {
    const result = await makeRequest(`${this.path}keys/`, {
      params: {},
    });

    console.log('keys', result);

    this.keys = result;

    return result;
  }

  @action
  public async getValuesForKey(keyId: string) {
    const result = await makeRequest(`${this.path}id/${keyId}`, {
      params: {},
    });

    this.values = {
      ...this.values,
      [result.key.repr]: result.values,
    };

    console.log('getValuesForKey', keyId, toJS(this.values));

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

  public async addValue(keyId: LabelKey['id'], value: string) {
    const result = await makeRequest(`${this.path}id/${keyId}/values`, {
      method: 'POST',
      data: { repr: value },
    });

    console.log('addValue', keyId, value, result);

    return result;
  }
}
