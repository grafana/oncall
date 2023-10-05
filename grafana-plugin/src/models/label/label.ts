import { noop } from 'lodash-es';
import { action, observable } from 'mobx';

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
  public async loadKeys(errorFn) {
    const result = await makeRequest(`${this.path}keys/`, {}).catch(errorFn);

    this.keys = result;

    return result;
  }

  @action
  public async loadValuesForKey(key: LabelKey['id'], search = '', errorFn = noop) {
    if (!key) {
      return [];
    }

    const result = await makeRequest(`${this.path}id/${key}`, {
      params: { search },
    }).catch(errorFn);

    const filteredValues = result.values.filter((v) => v.repr.toLowerCase().includes(search.toLowerCase())); // TODO remove after backend search implementation

    this.values = {
      ...this.values,
      [key]: filteredValues,
    };

    return filteredValues;
  }

  public async createKey(name: string) {
    const { key } = await makeRequest(`${this.path}`, {
      method: 'POST',
      data: { key: { repr: name }, values: [] },
    });

    return key;
  }

  public async createValue(keyId: LabelKey['id'], value: string) {
    const result = await makeRequest(`${this.path}id/${keyId}/values`, {
      method: 'POST',
      data: { repr: value },
    });

    return result.values.find((v) => v.repr === value); // TODO remove after backend API change
  }

  @action
  public async updateKey(keyId: LabelKey['id'], name: string) {
    const result = await makeRequest(`${this.path}id/${keyId}`, {
      method: 'PUT',
      data: { repr: name },
    });

    return result.key;
  }

  @action
  public async updateKeyValue(keyId: LabelKey['id'], valueId: LabelValue['id'], name: string) {
    const result = await makeRequest(`${this.path}id/${keyId}/values/${valueId}`, {
      method: 'PUT',
      data: { repr: name },
    });

    return result.values.find((v) => v.repr === name);
  }
}
