import { action, observable, runInAction } from 'mobx';

import BaseStore from 'models/base_store';
import { makeRequest } from 'network';
import { ApiSchemas } from 'network/oncall-api/api.types';
import onCallApi from 'network/oncall-api/http-client';
import { RootStore } from 'state';
import { openNotification } from 'utils';

export class LabelStore extends BaseStore {
  @observable.shallow
  public keys: Array<ApiSchemas['LabelKey']> = [];

  @observable.shallow
  public values: { [key: string]: Array<ApiSchemas['LabelValue']> } = {};

  constructor(rootStore: RootStore) {
    super(rootStore);

    this.path = '/labels/';
  }

  @action
  public async loadKeys() {
    const { data } = await onCallApi.GET('/labels/keys/', undefined);

    runInAction(() => {
      this.keys = data;
    });

    return data;
  }

  @action
  public async loadValuesForKey(key: ApiSchemas['LabelKey']['id'], search = '') {
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

  public async createValue(keyId: ApiSchemas['LabelKey']['id'], value: string) {
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
  public async updateKey(keyId: ApiSchemas['LabelKey']['id'], name: string) {
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
  public async updateKeyValue(
    keyId: ApiSchemas['LabelKey']['id'],
    valueId: ApiSchemas['LabelValue']['id'],
    name: string
  ) {
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
