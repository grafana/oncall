import { action, makeObservable } from 'mobx';

import { BaseStore } from 'models/base_store';
import { makeRequest } from 'network/network';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { onCallApi } from 'network/oncall-api/http-client';
import { RootStore } from 'state/rootStore';
import { WithGlobalNotification } from 'utils/decorators';

export class LabelStore extends BaseStore {
  constructor(rootStore: RootStore) {
    super(rootStore);

    makeObservable(this);

    this.path = '/labels/';
  }

  @action.bound
  public async loadKeys(search = '') {
    const { data } = await onCallApi().GET('/labels/keys/', undefined);

    const filtered = data.filter((k) => k.name.toLowerCase().includes(search.toLowerCase()));

    return filtered;
  }

  @action.bound
  async loadValuesForKey(key: ApiSchemas['LabelKey']['id'], search = '') {
    if (!key) {
      return [];
    }

    const result = await makeRequest(`${this.path}id/${key}`, {
      params: { search },
    });

    const filteredValues = result.values.filter((v) => v.name.toLowerCase().includes(search.toLowerCase()));

    return { ...result, values: filteredValues };
  }

  @WithGlobalNotification({ success: 'New key has been added', failure: 'Failed to add new key' })
  @action.bound
  async createKey(name: string) {
    const data = await makeRequest(`${this.path}`, {
      method: 'POST',
      data: { key: { name }, values: [] },
    });
    return data.key;
  }

  @WithGlobalNotification({ success: 'New value has been added', failure: 'Failed to add new value' })
  @action.bound
  async createValue(keyId: ApiSchemas['LabelKey']['id'], value: string) {
    const result = await makeRequest(`${this.path}id/${keyId}/values`, {
      method: 'POST',
      data: { name: value },
    });
    return result.values.find((v) => v.name === value); // TODO remove after backend API change
  }

  @WithGlobalNotification({ success: 'Key has been renamed', failure: 'Failed to rename key' })
  @action.bound
  async updateKey(keyId: ApiSchemas['LabelKey']['id'], name: string) {
    const result = await makeRequest(`${this.path}id/${keyId}`, {
      method: 'PUT',
      data: { name },
    });
    return result.key;
  }

  @WithGlobalNotification({ success: 'Value has been renamed', failure: 'Failed to rename value' })
  @action.bound
  async updateKeyValue(keyId: ApiSchemas['LabelKey']['id'], valueId: ApiSchemas['LabelValue']['id'], name: string) {
    const result = await makeRequest(`${this.path}id/${keyId}/values/${valueId}`, {
      method: 'PUT',
      data: { name },
    });
    return result.values.find((v) => v.name === name);
  }
}
