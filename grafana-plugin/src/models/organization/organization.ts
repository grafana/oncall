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

  @action.bound
  async loadCurrentOrganization() {
    const organization = await makeRequest(this.path, {});
    this.currentOrganization = organization;
  }

  @action
  async saveCurrentOrganization(data: Partial<Organization>) {
    this.currentOrganization = await makeRequest(this.path, {
      method: 'PUT',
      data,
    });
  }
}
