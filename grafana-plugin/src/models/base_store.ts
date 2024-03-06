import { sentenceCase } from 'change-case';
import { action } from 'mobx';

import { makeRequest } from 'network/network';
import { RootStore } from 'state/rootStore';
import { openWarningNotification } from 'utils/utils';

export class BaseStore {
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
              .map((key) => {
                const candidate = `${sentenceCase(key)}: ${payload[key]}`;
                if (candidate.includes('object Object')) {
                  return undefined;
                }
                return candidate;
              })
              .join('\n');

      if (text?.length) {
        openWarningNotification(text);
      }
    }

    throw error;
  }

  @action.bound
  async getAll(query = '') {
    return await makeRequest(`${this.path}`, {
      params: { search: query },
      method: 'GET',
    }).catch(this.onApiError);
  }

  @action.bound
  async getById(id: string, skipErrorHandling = false, fromOrganization = false) {
    return await makeRequest(`${this.path}${id}`, {
      method: 'GET',
      params: { from_organization: fromOrganization },
    }).catch((error) => this.onApiError(error, skipErrorHandling));
  }

  @action.bound
  async create<RT = any>(data: any, skipErrorHandling = false): Promise<RT | void> {
    return await makeRequest<RT>(this.path, {
      method: 'POST',
      data,
    }).catch((error) => {
      this.onApiError(error, skipErrorHandling);
    });
  }

  @action.bound
  async update<RT = any>(id: any, data: any, params: any = null, skipErrorHandling = false): Promise<RT | void> {
    const result = await makeRequest<RT>(`${this.path}${id}/`, {
      method: 'PUT',
      data,
      params: params,
    }).catch((error) => {
      this.onApiError(error, skipErrorHandling);
    });

    // Update env_status field for current team
    await this.rootStore.organizationStore.loadCurrentOrganization();
    return result;
  }

  @action.bound
  async delete(id: any) {
    const result = await makeRequest(`${this.path}${id}/`, {
      method: 'DELETE',
    }).catch(this.onApiError);

    // Update env_status field for current team
    await this.rootStore.organizationStore.loadCurrentOrganization();
    return result;
  }
}
