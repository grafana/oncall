import { action, observable } from 'mobx';

import BaseStore from 'models/base_store';
import { makeRequest } from 'network';
import { RootStore } from 'state';

import { getApiPathByPage } from './filters.helpers';
import { FilterOption } from './filters.types';

export class FiltersStore extends BaseStore {
  @observable.shallow
  public options: { [page: string]: FilterOption[] } = {};

  @observable.shallow
  public values: { [page: string]: Array<{ [key: string]: any }> } = {};

  constructor(rootStore: RootStore) {
    super(rootStore);
  }

  @action
  public async updateOptionsForPage(page: string) {
    const result = await makeRequest(`/${getApiPathByPage(page)}/filters/`, {});

    const allowFreeSearch = result.some((filter: FilterOption) => filter.name === 'search');
    if (!allowFreeSearch) {
      result.unshift({ name: 'search', type: 'search' });
    }

    this.options = {
      ...this.options,
      [page]: result,
    };

    return result;
  }

  @action
  updateValuesForPage(page: string, value: any) {
    this.values = {
      ...this.values,
      [page]: value,
    };
  }
}
