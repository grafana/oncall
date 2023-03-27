import { action, observable } from 'mobx';

import BaseStore from 'models/base_store';
import { makeRequest } from 'network';
import { RootStore } from 'state';
import { getItem, setItem } from 'utils/localStorage';

import { getApiPathByPage } from './filters.helpers';
import { FilterOption, FiltersValues } from './filters.types';

const LOCAL_STORAGE_FILTERS_KEY = 'grafana.oncall.global-filters';

export class FiltersStore extends BaseStore {
  @observable.shallow
  public options: { [page: string]: FilterOption[] } = {};

  @observable.shallow
  public values: { [page: string]: FiltersValues } = {};

  private _globalValues: FiltersValues = {};

  constructor(rootStore: RootStore) {
    super(rootStore);

    const savedFilters = getItem(LOCAL_STORAGE_FILTERS_KEY);
    if (savedFilters) {
      this._globalValues = { ...savedFilters };
    }
  }

  set globalValues(value: any) {
    this._globalValues = value;

    setItem(LOCAL_STORAGE_FILTERS_KEY, value);
  }

  get globalValues() {
    return this._globalValues;
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
  updateValuesForPage(page: string, value: FiltersValues) {
    this.values = {
      ...this.values,
      [page]: value,
    };
  }
}
