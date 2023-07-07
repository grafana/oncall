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
  async getAll<RT = any>(query = ''): Promise<void | RT> {
    return await makeRequest(`${this.path}`, {
      params: { search: query },
      method: 'GET',
    }).catch(this.onApiError);
  }

  @action
  async getById<RT = any>(id: string, skipErrorHandling = false, fromOrganization = false): Promise<void | RT> {
    return await makeRequest<RT>(`${this.path}${id}`, {
      method: 'GET',
      params: { from_organization: fromOrganization },
    }).catch((error) => this.onApiError(error, skipErrorHandling));
  }

  @action
  async create<RT = any>(data: any): Promise<void | RT> {
    return await makeRequest<RT>(this.path, {
      method: 'POST',
      data,
    }).catch(this.onApiError);
  }

  @action
  async update<RT = any>(id: any, data: any, params: any = null): Promise<void | RT> {
    const result = await makeRequest<RT>(`${this.path}${id}/`, {
      method: 'PUT',
      data,
      params: params,
    }).catch(this.onApiError);

    // Update env_status field for current team
    await this.rootStore.teamStore.loadCurrentTeam();
    return result;
  }

  @action
  async delete(id: any): Promise<void> {
    await makeRequest<void>(`${this.path}${id}/`, {
      method: 'DELETE',
    }).catch(this.onApiError);

    // Update env_status field for current team
    await this.rootStore.teamStore.loadCurrentTeam();
  }
}
