import { action, observable, makeObservable, runInAction } from 'mobx';

import { BaseStore } from 'models/base_store';
import { makeRequest } from 'network/network';
import { RootStore } from 'state/rootStore';

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

  @observable
  incidentFilters: any;

  constructor(rootStore: RootStore) {
    super(rootStore);

    makeObservable(this);

    this.path = '/escalation_chains/';
  }

  @action.bound
  async loadItem(id: EscalationChain['id'], skipErrorHandling = false): Promise<EscalationChain> {
    const escalationChain = await this.getById(id, skipErrorHandling);

    runInAction(() => {
      this.items = {
        ...this.items,
        [id]: escalationChain,
      };
    });

    return escalationChain;
  }

  @action.bound
  async updateById(id: EscalationChain['id']) {
    const response = await this.getById(id);

    runInAction(() => {
      this.items = {
        ...this.items,
        [id]: response,
      };
    });
  }

  @action.bound
  async save(id: EscalationChain['id'], data: Partial<EscalationChain>) {
    const response = await super.update(id, data);

    runInAction(() => {
      this.items = {
        ...this.items,
        [id]: response,
      };
    });
  }

  @action.bound
  async updateEscalationChainDetails(id: EscalationChain['id']) {
    const response = await makeRequest(`${this.path}${id}/details/`, {});

    runInAction(() => {
      this.details = {
        ...this.details,
        [id]: response,
      };
    });
  }

  @action.bound
  async updateItem(id: EscalationChain['id'], skipErrorHandling = false): Promise<EscalationChain> {
    let escalationChain;
    try {
      escalationChain = await this.getById(id, skipErrorHandling);
    } catch (error) {
      if (error.response.data?.error_code === 'wrong_team') {
        escalationChain = {
          id,
          name: '🔒 Private escalation chain',
          private: true,
        };
      }
    }

    if (escalationChain) {
      runInAction(() => {
        this.items = {
          ...this.items,
          [id]: escalationChain,
        };
      });
    }

    return escalationChain;
  }

  @action.bound
  async updateItems(query: any = '') {
    const params = typeof query === 'string' ? { search: query } : query;

    this.loading = true;

    const results = await makeRequest(`${this.path}`, {
      params,
    });

    runInAction(() => {
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

      const key = typeof query === 'string' ? query : '';

      this.searchResult = {
        ...this.searchResult,
        [key]: results.map((item: EscalationChain) => item.id),
      };
    });

    this.loading = false;
  }

  getSearchResult = (query = '') => {
    if (!this.searchResult[query]) {
      return undefined;
    }

    return this.searchResult[query].map((escalationChainId: EscalationChain['id']) => this.items[escalationChainId]);
  };

  clone = (escalationChainId: EscalationChain['id'], data: Partial<EscalationChain>): Promise<EscalationChain> =>
    makeRequest<EscalationChain>(`${this.path}${escalationChainId}/copy/`, {
      method: 'POST',
      data,
    });
}
