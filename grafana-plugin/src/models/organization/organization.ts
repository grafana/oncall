import { action, observable, makeObservable, runInAction } from 'mobx';

import { BaseStore } from 'models/base_store';
import { makeRequest } from 'network/network';
import { RootStore } from 'state/rootStore';

import { Organization, OrganizationConfigChecks } from './organization.types';

export class OrganizationStore extends BaseStore {
  @observable
  currentOrganization?: Organization;

  @observable
  organizationConfigChecks?: OrganizationConfigChecks;

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
  async loadCurrentOrganizationConfigChecks() {
    const organizationConfigChecks = await makeRequest(`${this.path}config-checks`, {});

    runInAction(() => {
      this.organizationConfigChecks = organizationConfigChecks;
    });
  }

  async saveCurrentOrganization(data: Partial<Organization>) {
    this.currentOrganization = await makeRequest(this.path, {
      method: 'PUT',
      data,
    });
  }
}
