import { action, observable, makeObservable, runInAction } from 'mobx';

import { BaseStore } from 'models/base_store';
import { LabelKeyValue } from 'models/label/label.types';
import { makeRequest } from 'network/network';
import { RootStore } from 'state/rootStore';
import { LocationHelper } from 'utils/LocationHelper';
import { PAGE } from 'utils/consts';
import { getItem, setItem } from 'utils/localStorage';

import { getApiPathByPage } from './filters.helpers';
import { FilterOption, FiltersValues } from './filters.types';

const LOCAL_STORAGE_FILTERS_KEY = 'grafana.oncall.global-filters';

export class FiltersStore extends BaseStore {
  @observable.shallow
  public options: { [page: string]: FilterOption[] } = {};

  @observable.shallow
  public values: { [page: string]: FiltersValues } = {};

  @observable.shallow
  public currentTablePageNum: { [page: string]: number } = {};

  private _globalValues: FiltersValues = {};

  @observable
  needToParseFilters = false;

  constructor(rootStore: RootStore) {
    super(rootStore);

    makeObservable(this);

    const savedFilters = getItem(LOCAL_STORAGE_FILTERS_KEY);
    if (savedFilters) {
      this._globalValues = { ...savedFilters };
    }
  }

  @action.bound
  setNeedToParseFilters(value: boolean) {
    this.needToParseFilters = value;
  }

  set globalValues(value: any) {
    this._globalValues = value;

    setItem(LOCAL_STORAGE_FILTERS_KEY, value);
  }

  get globalValues() {
    return this._globalValues;
  }

  @action.bound
  public async updateOptionsForPage(page: string) {
    const result = await makeRequest(`/${getApiPathByPage(page)}/filters/`, {});

    const allowFreeSearch = result.some((filter: FilterOption) => filter.name === 'search');
    if (!allowFreeSearch) {
      result.unshift({ name: 'search', type: 'search' });
    }

    runInAction(() => {
      this.options = {
        ...this.options,
        [page]: result,
      };
    });

    return result;
  }

  @action.bound
  updateValuesForPage(page: string, value: FiltersValues) {
    this.values = {
      ...this.values,
      [page]: value,
    };
  }

  @action.bound
  setCurrentTablePageNum(page: PAGE, currentTablePageNum: number) {
    this.currentTablePageNum[page] = currentTablePageNum;
  }

  @action.bound
  applyLabelFilter = (label: LabelKeyValue, page: PAGE) => {
    const currentLabelFilterValues = this.values[page]?.label || [];
    const labelToAddString = `${label.key.id}:${label.value.id}`;
    const newLabelFilter = [...currentLabelFilterValues, labelToAddString];

    if (currentLabelFilterValues?.some((label) => label === labelToAddString)) {
      return;
    }

    this.updateValuesForPage(page, {
      label: newLabelFilter,
    });
    LocationHelper.update({ label: newLabelFilter }, 'partial');
    this.setNeedToParseFilters(true);
  };
}
