import { action, observable, makeObservable, runInAction } from 'mobx';

import BaseStore from 'models/base_store';
import { makeRequest } from 'network';
import { RootStore } from 'state';

import { Organization } from './organization.types';

export class OrganizationStore extends BaseStore {
  @observable
  currentOrganization?: Organization;

  constructor(rootStore: RootStore) {
    super(rootStore);
    makeObservable(this);
    this.path = '/organization/';
  }

  @action.bound
  async loadCurrentOrganization() {
    const organization = await makeRequest(this.path, {});

    runInAction(() => {
      this.currentOrganization = organization;
    });
  }

  @action.bound
  async saveCurrentOrganization(data: Partial<Organization>) {
    this.currentOrganization = await makeRequest(this.path, {
      method: 'PUT',
      data,
    });
  }
}
