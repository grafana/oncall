import React, { Component } from 'react';

import { KeyValue, SelectableValue, TimeRange } from '@grafana/data';
import {
  InlineSwitch,
  MultiSelect,
  TimeRangeInput,
  Select,
  LoadingPlaceholder,
  Input,
  Icon,
  Tooltip,
  Button,
} from '@grafana/ui';
import { capitalCase } from 'change-case';
import cn from 'classnames/bind';
import { debounce, isUndefined, omitBy, pickBy } from 'lodash-es';
import { observer } from 'mobx-react';
import moment from 'moment-timezone';
import Emoji from 'react-emoji-render';

import { Text } from 'components/Text/Text';
import { LabelsFilter } from 'containers/Labels/LabelsFilter';
import { RemoteSelect } from 'containers/RemoteSelect/RemoteSelect';
import { TeamName } from 'containers/TeamName/TeamName';
import { FiltersValues } from 'models/filters/filters.types';
import { GrafanaTeamStore } from 'models/grafana_team/grafana_team';
import { SelectOption, WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import { LocationHelper } from 'utils/LocationHelper';
import { PAGE } from 'utils/consts';
import { convertTimerangeToFilterValue, getValueForDateRangeFilterType } from 'utils/datetime';
import { allFieldsEmpty } from 'utils/utils';

import { parseFilters } from './RemoteFilters.helpers';
import { FilterOption } from './RemoteFilters.types';

import styles from './RemoteFilters.module.css';

const cx = cn.bind(styles);

interface RemoteFiltersProps extends WithStoreProps {
  onChange: (filters: Record<string, any>, isOnMount: boolean, invalidateFn: () => boolean) => void;
  query: KeyValue;
  page: PAGE;
  defaultFilters?: FiltersValues;
  extraFilters?: (state, setState, onFiltersValueChange) => React.ReactNode;
  grafanaTeamStore: GrafanaTeamStore;
  skipFilterOptionFn?: (filterOption: FilterOption) => boolean;
}
export interface RemoteFiltersState {
  filterOptions?: FilterOption[];
  filters: FilterOption[];
  values: Record<string, any>;
  hadInteraction: boolean;
  lastRequestId: string;
}

@observer
class _RemoteFilters extends Component<RemoteFiltersProps, RemoteFiltersState> {
  state: RemoteFiltersState = {
    filterOptions: undefined,
    filters: undefined,
    values: {},
    hadInteraction: false,
    lastRequestId: undefined,
  };

  searchRef = React.createRef<HTMLInputElement>();

  componentDidUpdate(prevProps: Readonly<RemoteFiltersProps>): void {
    const { store, query } = this.props;
    const { filtersStore } = store;

    if (prevProps.query !== query && filtersStore.needToParseFilters) {
      filtersStore.needToParseFilters = false;

      const { filterOptions } = this.state;

      let { filters, values } = parseFilters({ ...query, ...filtersStore.globalValues }, filterOptions, query);

      this.setState({ filterOptions, filters, values }, () => this.onChange());
    }
  }

  async componentDidMount() {
    const {
      query,
      page,
      store: { filtersStore },
      defaultFilters,
      skipFilterOptionFn,
    } = this.props;

    let filterOptions = await filtersStore.updateOptionsForPage(page);
    const currentTablePageNum = parseInt(filtersStore.currentTablePageNum[page] || query.p || 1, 10);

    if (skipFilterOptionFn) {
      filterOptions = filterOptions.filter((option: FilterOption) => !skipFilterOptionFn(option));
    }

    // set the current page from filters/query or default it to 1
    filtersStore.setCurrentTablePageNum(page, currentTablePageNum);

    let { filters, values } = parseFilters({ ...query, ...filtersStore.globalValues }, filterOptions, query);

    if (allFieldsEmpty(values)) {
      ({ filters, values } = parseFilters(defaultFilters, filterOptions, query));
    }

    this.setState({ filterOptions, filters, values }, () => this.onChange(true));
  }

  render() {
    const { extraFilters } = this.props;

    return (
      <div className={cx('root')}>
        {this.renderFilters()}
        {extraFilters && (
          <div className={cx('extra-filters')}>
            {extraFilters(this.state, this.setState.bind(this), this.onFiltersValueChange.bind(this))}
          </div>
        )}
      </div>
    );
  }

  renderFilters = () => {
    const { filters, filterOptions } = this.state;

    if (!filterOptions) {
      return <LoadingPlaceholder text="Loading filters..." />;
    }

    const options = filterOptions
      .filter(
        (item: FilterOption) =>
          item.type !== 'search' && !filters.some((filter: FilterOption) => filter.name === item.name)
      )
      .map((item: FilterOption) => ({
        label: item.display_name || capitalCase(item.name),
        value: item.name,
        data: item,
      }));

    const allowFreeSearch = filterOptions.some((filter: FilterOption) => filter.name === 'search');

    return (
      <div className={cx('filters')}>
        {filters.map((filterOption: FilterOption) => (
          <div key={filterOption.name} className={cx('filter')}>
            <Text type="secondary">{filterOption.display_name || capitalCase(filterOption.name)}</Text>
            {filterOption.description && (
              <Tooltip content={filterOption.description}>
                <Icon name="info-circle" />
              </Tooltip>
            )}
            <Text type="secondary">:</Text> {this.renderFilterOption(filterOption)}
            <Button
              size="sm"
              icon="times"
              tooltip="Remove filter"
              variant="secondary"
              onClick={this.getDeleteFilterClickHandler(filterOption.name)}
            />
          </div>
        ))}
        <Select
          menuShouldPortal
          key={filters.length}
          className={cx('filter-options')}
          placeholder="Search or filter results..."
          value={undefined}
          onChange={this.handleAddFilter}
          getOptionLabel={(item: SelectableValue) => capitalCase(item.label)}
          options={options}
          allowCustomValue={allowFreeSearch}
          onCreateOption={this.handleSearch}
          formatCreateLabel={(str) => `Search ${str}`}
        />
      </div>
    );
  };

  handleSearch = (query: string) => {
    const { filters } = this.state;

    const searchFilter = filters.find((filter: FilterOption) => filter.name === 'search');

    const newFilters = filters;
    if (!searchFilter) {
      newFilters.push({ name: 'search', type: 'search' });
    } else {
      this.searchRef.current.focus();
    }

    this.setState(
      {
        hadInteraction: true,
        filters: newFilters,
      },
      () => {
        this.onFiltersValueChange('search', query);
      }
    );
  };

  getDeleteFilterClickHandler = (filterName: FilterOption['name']) => {
    const { filters } = this.state;

    return () => {
      const newFilters = filters.filter((filterOption: FilterOption) => filterOption.name !== filterName);

      this.setState({ filters: newFilters });

      LocationHelper.update({ [filterName]: undefined }, 'partial');

      this.onFiltersValueChange(filterName, undefined);
    };
  };

  handleAddFilter = (option: SelectableValue) => {
    const { filters } = this.state;

    this.setState({
      filters: [...filters, option.data],
      hadInteraction: true,
    });

    if (option.data.default) {
      let defaultValue = option.data.default;
      if (option.data.type === 'options') {
        defaultValue = [option.data.default.value];
      }
      if (option.data.type === 'boolean') {
        defaultValue = defaultValue === 'false' ? false : Boolean(defaultValue);
      }

      this.onFiltersValueChange(option.value, defaultValue);
    }
  };

  renderFilterOption = (filter: FilterOption) => {
    const { values, hadInteraction } = this.state;
    const { grafanaTeamStore } = this.props;

    const autoFocus = Boolean(hadInteraction);
    switch (filter.type) {
      case 'options':
        if (filter.options) {
          return (
            <MultiSelect
              autoFocus={autoFocus}
              openMenuOnFocus
              className={cx('filter-select')}
              options={filter.options.map((option: SelectOption) => ({
                label: option.display_name,
                value: option.value,
              }))}
              value={values[filter.name]}
              onChange={this.getOptionsFilterChangeHandler(filter.name)}
            />
          );
        }

        return (
          <RemoteSelect
            autoFocus={autoFocus}
            className={cx('filter-select')}
            isMulti
            fieldToShow="display_name"
            valueField="value"
            href={filter.href.replace('/api/internal/v1', '')}
            value={values[filter.name]}
            onChange={this.getRemoteOptionsChangeHandler(filter.name)}
            getOptionLabel={(item: SelectableValue) => <Emoji text={item.label || ''} />}
            predefinedOptions={filter.default ? [filter.default] : undefined}
          />
        );

      case 'boolean':
        return (
          <InlineSwitch
            autoFocus={hadInteraction}
            transparent
            value={values[filter.name]}
            onChange={this.getBooleanFilterChangeHandler(filter.name)}
          />
        );

      case 'search':
        return (
          <Input
            ref={this.searchRef}
            autoFocus={autoFocus}
            value={values[filter.name]}
            onChange={this.getSearchFilterChangeHandler(filter.name)}
          />
        );

      case 'team_select':
        return (
          <RemoteSelect
            autoFocus={autoFocus}
            className={cx('filter-select')}
            isMulti
            fieldToShow="name"
            valueField="id"
            href={filter.href.replace('/api/internal/v1', '')}
            value={values[filter.name]}
            onChange={this.getRemoteOptionsChangeHandler(filter.name)}
            getOptionLabel={(item: SelectableValue) => <TeamName team={grafanaTeamStore.items[item.value]} />}
          />
        );

      case 'daterange':
        const value = getValueForDateRangeFilterType(values[filter.name]);

        return (
          <TimeRangeInput
            timeZone={moment.tz.guess()}
            value={value}
            onChange={this.getDateRangeFilterChangeHandler(filter.name)}
            hideTimeZone
            clearable={false}
          />
        );

      case 'labels':
      case 'alert_group_labels':
        return (
          <LabelsFilter
            filterType={filter.type}
            autoFocus={autoFocus}
            className={cx('filter-select')}
            value={values[filter.name]}
            onChange={this.getLabelsFilterChangeHandler(filter.name)}
          />
        );

      default:
        console.warn('Unknown type of filter:', filter.type, 'with name', filter.name);
        return null;
    }
  };

  getOptionsFilterChangeHandler = (name: FilterOption['name']) => {
    return (options: SelectableValue[]) => {
      this.onFiltersValueChange(
        name,
        options.map((option) => option.value)
      );
    };
  };

  getLabelsFilterChangeHandler = (name: FilterOption['name']) => {
    return (options: Array<{ key: SelectableValue; value: SelectableValue }>) => {
      this.onFiltersValueChange(
        name,
        options.map((option) => `${option.key.id}:${option.value.id}`)
      );
    };
  };

  getRemoteOptionsChangeHandler = (name: FilterOption['name']) => {
    return (value: SelectableValue[], _items: any[]) => {
      this.onFiltersValueChange(name, value);
    };
  };

  getBooleanFilterChangeHandler = (name: FilterOption['name']) => {
    return (event: React.ChangeEvent<HTMLInputElement>) => {
      this.onFiltersValueChange(name, event.target.checked);
    };
  };

  getDateRangeFilterChangeHandler = (name: FilterOption['name']) => {
    return (timeRange: TimeRange) => {
      const value = convertTimerangeToFilterValue(timeRange);
      this.onFiltersValueChange(name, value);
    };
  };

  onFiltersValueChange = (name: FilterOption['name'], value: any) => {
    const { values } = this.state;

    const newValues = omitBy({ ...values, [name]: value }, isUndefined);

    this.setState({ values: newValues }, this.debouncedOnChange);
  };

  getSearchFilterChangeHandler = (name: FilterOption['name']) => {
    return (event: React.ChangeEvent<HTMLInputElement>) => {
      const text = event.target.value;
      this.onFiltersValueChange(name, text);
    };
  };

  getTeamSelectFilterChangeHandler = (name: FilterOption['name']) => {
    return (value: any) => {
      const text = value;
      this.onFiltersValueChange(name, text);
    };
  };

  onChange = (isOnMount = false) => {
    const { store, page, onChange } = this.props;
    const { values, filterOptions } = this.state;

    store.filtersStore.updateValuesForPage(page, values);

    if (!isOnMount) {
      // Skip updating local storage for mounting, this way URL won't overwrite local storage but subsequent actions WILL do
      Object.keys({ ...store.filtersStore.globalValues }).forEach((key) => {
        if (!(key in values)) {
          delete store.filtersStore.globalValues[key];
        }
      });

      const newGlobalValues = pickBy(values, (_, key) =>
        filterOptions.some((option) => option.name === key && option.global)
      );

      store.filtersStore.globalValues = newGlobalValues;
    }

    const currentRequestId = this.getNewRequestId();
    this.setState({ lastRequestId: currentRequestId });

    LocationHelper.update({ ...values }, 'partial');
    onChange(values, isOnMount, this.invalidateFn.bind(this, currentRequestId));
  };

  invalidateFn = (id: string) => {
    const { lastRequestId } = this.state;

    // This will ensure that only the newest request will get to update the store data
    return lastRequestId && id !== lastRequestId;
  };

  getNewRequestId = () => Math.random().toString(36).slice(-6);

  debouncedOnChange = debounce(this.onChange, 500);
}

export const RemoteFilters = withMobXProviderContext(_RemoteFilters) as unknown as React.ComponentClass<
  Omit<RemoteFiltersProps, 'store'>
>;
