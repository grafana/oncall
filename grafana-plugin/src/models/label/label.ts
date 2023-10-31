import { action, observable } from 'mobx';

import BaseStore from 'models/base_store';
import { makeRequest } from 'network';
import { RootStore } from 'state';
import { openNotification } from 'utils';

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
  public async loadKeys() {
    const result = await makeRequest(`${this.path}keys/`, {});

    this.keys = result;

    return result;
  }

  @action
  public async loadValuesForKey(key: LabelKey['id'], search = '') {
    if (!key) {
      return [];
    }

    const result = await makeRequest(`${this.path}id/${key}`, {
      params: { search },
    });

    const filteredValues = result.values.filter((v) => v.name.toLowerCase().includes(search.toLowerCase())); // TODO remove after backend search implementation

    this.values = {
      ...this.values,
      [key]: filteredValues,
    };

    return { ...result, values: filteredValues };
  }

  public async createKey(name: string) {
    const { key } = await makeRequest(`${this.path}`, {
      method: 'POST',
      data: { key: { name }, values: [] },
    }).then((data) => {
      openNotification(`New key has been added`);

      return data;
    });

    return key;
  }

  public async createValue(keyId: LabelKey['id'], value: string) {
    const result = await makeRequest(`${this.path}id/${keyId}/values`, {
      method: 'POST',
      data: { name: value },
    }).then((data) => {
      openNotification(`New value has been added`);

      return data;
    });

    return result.values.find((v) => v.name === value); // TODO remove after backend API change
  }

  @action
  public async updateKey(keyId: LabelKey['id'], name: string) {
    const result = await makeRequest(`${this.path}id/${keyId}`, {
      method: 'PUT',
      data: { name },
    }).then((data) => {
      openNotification(`Key has been renamed`);

      return data;
    });

    return result.key;
  }

  @action
  public async updateKeyValue(keyId: LabelKey['id'], valueId: LabelValue['id'], name: string) {
    const result = await makeRequest(`${this.path}id/${keyId}/values/${valueId}`, {
      method: 'PUT',
      data: { name },
    }).then((data) => {
      openNotification(`Value has been renamed`);

      return data;
    });

    return result.values.find((v) => v.name === name);
  }
}
