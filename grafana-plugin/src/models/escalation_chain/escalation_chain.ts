import { action, observable } from 'mobx';

import BaseStore from 'models/base_store';
import { makeRequest } from 'network';
import { RootStore } from 'state';

import { EscalationChain, EscalationChainDetails } from './escalation_chain.types';

export class EscalationChainStore extends BaseStore {
  @observable.shallow
  items: { [id: string]: EscalationChain } = {};

  @observable.shallow
  details: { [id: string]: EscalationChainDetails[] } = {};

  @observable.shallow
  searchResult: { [key: string]: Array<EscalationChain['id']> } = {};

  @observable
  loading = false;

  constructor(rootStore: RootStore) {
    super(rootStore);

    this.path = '/escalation_chains/';
  }

  @action
  async loadItem(id: EscalationChain['id'], skipErrorHandling = false): Promise<EscalationChain> {
    const escalationChain = await this.getById(id, skipErrorHandling);

    this.items = {
      ...this.items,
      [id]: escalationChain,
    };

    return escalationChain;
  }

  @action
  async updateById(id: EscalationChain['id']) {
    const response = await this.getById(id);

    this.items = {
      ...this.items,
      [id]: response,
    };
  }

  @action
  async save(id: EscalationChain['id'], data: Partial<EscalationChain>) {
    const response = await super.update(id, data);

    this.items = {
      ...this.items,
      [id]: response,
    };
  }

  @action
  async updateEscalationChainDetails(id: EscalationChain['id']) {
    const response = await makeRequest(`${this.path}${id}/details/`, {});

    this.details = {
      ...this.details,
      [id]: response,
    };
  }

  @action
  async updateItems(query = '') {
    this.loading = true;

    const results = await makeRequest(`${this.path}`, {
      params: { search: query },
    });

    this.items = {
      ...this.items,
      ...results.reduce(
        (acc: { [key: number]: EscalationChain }, item: EscalationChain) => ({
          ...acc,
          [item.id]: item,
        }),
        {}
      ),
    };

    this.searchResult = {
      ...this.searchResult,
      [query]: results.map((item: EscalationChain) => item.id),
    };

    this.loading = false;
  }

  getSearchResult(query = '') {
    if (!this.searchResult[query]) {
      return undefined;
    }

    return this.searchResult[query].map((escalationChainId: EscalationChain['id']) => this.items[escalationChainId]);
  }

  async clone(escalationChainId: EscalationChain['id'], data: Partial<EscalationChain>) {
    return await makeRequest(`${this.path}${escalationChainId}/copy/`, {
      method: 'POST',
      data,
    });
  }
}
