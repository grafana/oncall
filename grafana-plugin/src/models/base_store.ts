import { sentenceCase } from 'change-case';
import { action } from 'mobx';

import { makeRequest } from 'network';
import { RootStore } from 'state';
import { openWarningNotification } from 'utils';

export default class BaseStore {
  protected rootStore: RootStore;
  protected path = '';

  constructor(rootStore: RootStore) {
    this.rootStore = rootStore;
  }

  onApiError(error: any, skipErrorHandling = false) {
    if (skipErrorHandling) {
      throw error; // rethrow error and skip additional handling like showing notification
    }

    if (error.response.status >= 400 && error.response.status < 500) {
      const payload = error.response.data;
      const text =
        typeof payload === 'string'
          ? payload
          : Object.keys(payload)
              .map((key) => `${sentenceCase(key)}: ${payload[key]}`)
              .join('\n');
      openWarningNotification(text);
    }

    throw error;
  }

  @action
  async getAll(query = '') {
    return await makeRequest(`${this.path}`, {
      params: { search: query },
      method: 'GET',
    }).catch(this.onApiError);
  }

  @action
  async getById(id: string, skipErrorHandling = false, fromOrganization = false) {
    return await makeRequest(`${this.path}${id}`, {
      method: 'GET',
      params: { from_organization: fromOrganization },
    }).catch((error) => this.onApiError(error, skipErrorHandling));
  }

  @action
  async create(data: any) {
    return await makeRequest(this.path, {
      method: 'POST',
      data,
    }).catch(this.onApiError);
  }

  @action
  async update(id: any, data: any, params: any = null) {
    const result = await makeRequest(`${this.path}${id}/`, {
      method: 'PUT',
      data,
      params: params,
    }).catch(this.onApiError);

    // Update env_status field for current team
    await this.rootStore.teamStore.loadCurrentTeam();
    return result;
  }

  @action
  async delete(id: any) {
    const result = await makeRequest(`${this.path}${id}/`, {
      method: 'DELETE',
    }).catch(this.onApiError);

    // Update env_status field for current team
    await this.rootStore.teamStore.loadCurrentTeam();
    return result;
  }
}
