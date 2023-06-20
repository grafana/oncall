import React, { Component } from 'react';

import { SelectableValue, TimeRange } from '@grafana/data';
import {
  IconButton,
  InlineSwitch,
  MultiSelect,
  TimeRangeInput,
  Select,
  LoadingPlaceholder,
  Input,
  Icon,
  Tooltip,
} from '@grafana/ui';
import { capitalCase } from 'change-case';
import cn from 'classnames/bind';
import { debounce, isEmpty, isUndefined, omitBy, pickBy } from 'lodash-es';
import { observer } from 'mobx-react';
import moment from 'moment-timezone';
import Emoji from 'react-emoji-render';

import Text from 'components/Text/Text';
import RemoteSelect from 'containers/RemoteSelect/RemoteSelect';
import TeamName from 'containers/TeamName/TeamName';
import { FiltersValues } from 'models/filters/filters.types';
import { GrafanaTeamStore } from 'models/grafana_team/grafana_team';
import { SelectOption, WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import LocationHelper from 'utils/LocationHelper';

import { parseFilters } from './RemoteFilters.helpers';
import { FilterOption, RemoteFiltersType } from './RemoteFilters.types';

import styles from './RemoteFilters.module.css';

const cx = cn.bind(styles);

interface RemoteFiltersProps extends WithStoreProps {
  value: RemoteFiltersType;
  onChange: (filters: { [key: string]: any }, isOnMount: boolean) => void;
  query: { [key: string]: any };
  page: string;
  defaultFilters?: FiltersValues;
  extraFilters?: (state, setState, onFiltersValueChange) => React.ReactNode;
  grafanaTeamStore: GrafanaTeamStore;
}
interface RemoteFiltersState {
  filterOptions?: FilterOption[];
  filters: FilterOption[];
  values: { [key: string]: any };
  hadInteraction: boolean;
}

@observer
class RemoteFilters extends Component<RemoteFiltersProps, RemoteFiltersState> {
  state: RemoteFiltersState = {
    filterOptions: undefined,
    filters: undefined,
    values: {},
    hadInteraction: false,
  };

  searchRef = React.createRef<HTMLInputElement>();

  async componentDidMount() {
    const { query, page, store, defaultFilters } = this.props;

    const { filtersStore } = store;

    const filterOptions = await filtersStore.updateOptionsForPage(page);

    let { filters, values } = parseFilters({ ...query, ...filtersStore.globalValues }, filterOptions, query);

    if (isEmpty(values)) {
      ({ filters, values } = parseFilters(defaultFilters || { team: [] }, filterOptions, query));
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
            <IconButton size="sm" name="times" onClick={this.getDeleteFilterClickHandler(filterOption.name)} />
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
        const dates = values[filter.name] ? values[filter.name].split('/') : undefined;

        const value = {
          from: dates ? moment(dates[0] + 'Z') : undefined,
          to: dates ? moment(dates[1] + 'Z') : undefined,
          raw: {
            from: dates ? dates[0] : '',
            to: dates ? dates[1] : '',
          },
        };

        return (
          <TimeRangeInput
            timeZone={moment.tz.guess()}
            autoFocus={autoFocus}
            // @ts-ignore
            value={value}
            onChange={this.getDateRangeFilterChangeHandler(filter.name)}
            hideTimeZone
            clearable={false}
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
      const value =
        timeRange.from.utc().format('YYYY-MM-DDTHH:mm:ss') + '/' + timeRange.to.utc().format('YYYY-MM-DDTHH:mm:ss');

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

    LocationHelper.update({ ...values }, 'partial');
    onChange(values, isOnMount);
  };

  debouncedOnChange = debounce(this.onChange, 500);
}

export default withMobXProviderContext(RemoteFilters);
