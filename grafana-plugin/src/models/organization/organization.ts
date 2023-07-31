import { action, observable } from 'mobx';

import BaseStore from 'models/base_store';
import { makeRequest } from 'network';
import { RootStore } from 'state';

import { Organization } from './organization.types';

export class OrganizationStore extends BaseStore {
  @observable
  currentOrganization?: Organization;

  constructor(rootStore: RootStore) {
    super(rootStore);
    this.path = '/organization/';
  }

  @action
  async loadCurrentOrganization() {
    this.currentOrganization = await makeRequest(this.path, {});
  }

  @action
  async saveCurrentOrganization(data: Partial<Organization>) {
    this.currentOrganization = await makeRequest(this.path, {
      method: 'PUT',
      data,
    });
  }
}
