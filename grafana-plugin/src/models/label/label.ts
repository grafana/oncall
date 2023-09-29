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
  }

  @action
  public async loadKeys(search = '') {
    const result = (
      await makeRequest(`${this.path}keys/`, {
        params: { search },
      })
    ).filter((k) => k.repr.includes(search)); // TODO remove after backend search implementation

    this.keys = result;

    console.log('loadKeys', search, result);

    return result;
  }

  @action
  public async loadValuesForKey(key: LabelKey['id'], search = '') {
    const result = await makeRequest(`${this.path}id/${key}`, {
      params: { search },
    });

    const filteredValues = result.values.filter((v) => v.repr.includes(search)); // TODO remove after backend search implementation

    this.values = {
      ...this.values,
      [key]: filteredValues,
    };

    console.log('loadValuesForKey', key, search, result);

    return filteredValues;
  }

  public async createKey(name: string) {
    const { key } = await makeRequest(`${this.path}`, {
      method: 'POST',
      data: { key: { repr: name }, values: [] },
    });

    console.log('createKey', name, key);

    return key;
  }

  public async createValue(keyId: LabelKey['id'], value: string) {
    const result = await makeRequest(`${this.path}id/${keyId}/values`, {
      method: 'POST',
      data: { repr: value },
    });

    console.log('createValue', result);

    return result.values.find((v) => v.repr === value); // TODO remove after backend API change
  }

  @action
  public async updateKey(keyId: LabelKey['id'], name: string) {
    const result = await makeRequest(`${this.path}id/${keyId}`, {
      method: 'PUT',
      data: { repr: name },
    });

    console.log('updateKey', result);

    return result.key;
  }

  @action
  public async updateKeyValue(keyId: LabelKey['id'], valueId: LabelValue['id'], name: string) {
    const result = await makeRequest(`${this.path}id/${keyId}/values/${valueId}`, {
      method: 'PUT',
      data: { repr: name },
    });

    console.log('updateKeyValue', result);

    return result.values.find((v) => v.repr === name);
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

  public async addValue(keyId: LabelKey['id'], value: string) {
    const result = await makeRequest(`${this.path}id/${keyId}/values`, {
      method: 'POST',
      data: { repr: value },
    });

    console.log('addValue', keyId, value, result);

    return result;
  }
}
