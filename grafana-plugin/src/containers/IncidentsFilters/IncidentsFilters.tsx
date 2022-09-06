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
} from '@grafana/ui';
import { capitalCase } from 'change-case';
import cn from 'classnames/bind';
import { debounce, isEmpty, isUndefined, omitBy } from 'lodash-es';
import { observer } from 'mobx-react';
import moment from 'moment-timezone';
import Emoji from 'react-emoji-render';

import CardButton from 'components/CardButton/CardButton';
import Text from 'components/Text/Text';
import RemoteSelect from 'containers/RemoteSelect/RemoteSelect';
import { IncidentStatus } from 'models/alertgroup/alertgroup.types';
import { makeRequest } from 'network';
import { SelectOption, WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';

import { parseFilters } from './IncidentFilters.helpers';
import { FilterOption, IncidentsFiltersType } from './IncidentFilters.types';

import styles from './IncidentsFilters.module.css';

const cx = cn.bind(styles);

interface IncidentsFiltersProps extends WithStoreProps {
  value: IncidentsFiltersType;
  onChange: (filters: { [key: string]: any }, isOnMount: boolean) => void;
  query: { [key: string]: any };
}
interface IncidentsFiltersState {
  filterOptions?: FilterOption[];
  filters: FilterOption[];
  values: { [key: string]: any };
  hadInteraction: boolean;
}

@observer
class IncidentsFilters extends Component<IncidentsFiltersProps, IncidentsFiltersState> {
  state: IncidentsFiltersState = {
    filterOptions: undefined,
    filters: [],
    values: {},
    hadInteraction: false,
  };

  searchRef = React.createRef<HTMLInputElement>();

  async componentDidMount() {
    const { query, store } = this.props;

    const filterOptions = await makeRequest('/alertgroups/filters/', {});

    let { filters, values } = parseFilters(query, filterOptions);

    if (isEmpty(values)) {
      // TODO fill filters if no filters in query
      let newQuery;
      if (store.incidentFilters) {
        newQuery = { ...store.incidentFilters };
      } else {
        newQuery = {
          status: [IncidentStatus.New, IncidentStatus.Acknowledged],
        };
      }

      ({ filters, values } = parseFilters(newQuery, filterOptions));
    }

    this.setState({ filterOptions, filters, values }, () => {
      this.onChange(true);
    });
  }

  render() {
    return (
      <div className={cx('root')}>
        {this.renderFilters()}
        {this.renderCards()}
      </div>
    );
  }

  renderFilters = () => {
    const { store, value } = this.props;
    const { filterOptions, filters } = this.state;

    const filterNames = filters.map((filter: FilterOption) => filter.name);

    if (!filterOptions) {
      return <LoadingPlaceholder text="Loading filters..." />;
    }

    const options = filterOptions
      .filter(
        (item: FilterOption) =>
          item.type !== 'search' && !filters.some((filter: FilterOption) => filter.name === item.name)
      )
      .map((item: FilterOption) => ({ label: capitalCase(item.name), value: item.name, data: item }));

    return (
      <div className={cx('filters')}>
        {filters.map((filterOption: FilterOption) => (
          <div className={cx('filter')}>
            <Text type="secondary">{capitalCase(filterOption.name)}:</Text> {this.renderFilterOption(filterOption)}
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
          allowCustomValue
          onCreateOption={this.handleSearch}
          formatCreateLabel={(str) => `Search ${str}`}
        />
      </div>
    );
  };

  renderCards() {
    const { store } = this.props;
    const {
      teamStore: { currentTeam },
    } = store;

    const { values } = this.state;

    const { newIncidents, acknowledgedIncidents, resolvedIncidents, silencedIncidents } = store.alertGroupStore;

    const { count: newIncidentsCount, alert_group_rate_to_previous_same_period: newIncidentsRate } = newIncidents;

    const { count: acknowledgedIncidentsCount, alert_group_rate_to_previous_same_period: acknowledgedIncidentsRate } =
      acknowledgedIncidents;

    const { count: resolvedIncidentsCount, alert_group_rate_to_previous_same_period: resolvedIncidentsRate } =
      resolvedIncidents;

    const { count: silencedIncidentsCount, alert_group_rate_to_previous_same_period: silencedIncidentsRate } =
      silencedIncidents;

    const status = values.status || [];

    return (
      <div className={cx('cards', 'row')}>
        <div key="new" className={cx('col')}>
          <CardButton
            icon={<Icon name="bell" size="xxxl" />}
            description="New alert groups"
            title={newIncidentsCount}
            selected={status.includes(IncidentStatus.New)}
            onClick={this.getStatusButtonClickHandler(IncidentStatus.New)}
          />
        </div>
        <div key="acknowledged" className={cx('col')}>
          <CardButton
            icon={<Icon name="eye" size="xxxl" />}
            description="Acknowledged alert groups"
            title={acknowledgedIncidentsCount}
            selected={status.includes(IncidentStatus.Acknowledged)}
            onClick={this.getStatusButtonClickHandler(IncidentStatus.Acknowledged)}
          />
        </div>
        <div key="resolved" className={cx('col')}>
          <CardButton
            icon={<Icon name="check" size="xxxl" />}
            description="Resolved alert groups"
            title={resolvedIncidentsCount}
            selected={status.includes(IncidentStatus.Resolved)}
            onClick={this.getStatusButtonClickHandler(IncidentStatus.Resolved)}
          />
        </div>
        <div key="silenced" className={cx('col')}>
          <CardButton
            icon={<Icon name="bell-slash" size="xxxl" />}
            description="Silenced alert groups"
            title={silencedIncidentsCount}
            selected={status.includes(IncidentStatus.Silenced)}
            onClick={this.getStatusButtonClickHandler(IncidentStatus.Silenced)}
          />
        </div>
      </div>
    );
  }

  handleSearch = (query: string) => {
    const { filters, values } = this.state;

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
    const { filters, values } = this.state;

    return () => {
      const newFilters = filters.filter((filterOption: FilterOption) => filterOption.name !== filterName);

      this.setState({ filters: newFilters });

      this.onFiltersValueChange(filterName, undefined);
    };
  };

  handleAddFilter = (option: SelectableValue) => {
    const { value, onChange } = this.props;
    const { values, filters } = this.state;

    this.setState({
      filters: [...filters, option.data],
      hadInteraction: true,
    });

    if (option.data.default) {
      const defaultValue = option.data.type === 'options' ? [option.data.default.value] : option.data.default;

      this.onFiltersValueChange(option.value, defaultValue);
    }
  };

  renderFilterOption = (filter: FilterOption) => {
    const { values, filterOptions, hadInteraction } = this.state;

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
                label: capitalCase(option.display_name),
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

      case 'daterange':
        const dates = values[filter.name] ? values[filter.name].split('/') : undefined;

        const value = {
          from: dates ? moment(dates[0] + 'Z') : undefined,
          to: dates ? moment(dates[1] + 'Z') : undefined,
          /* raw: {
            from: dates ? moment(dates[0]).format('MMM DD, YYYY hh:mm A') : undefined,
            to: dates ? moment(dates[1]).format('MMM DD, YYYY hh:mm A') : undefined,
          },*/

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

  getStatusButtonClickHandler = (status: IncidentStatus) => {
    const { store } = this.props;
    return (selected: boolean) => {
      const { values } = this.state;

      const { status: statusFilter = [] } = values;

      let newStatuses = [...statusFilter];

      if (selected) {
        newStatuses.push(status);
      } else {
        newStatuses = newStatuses.filter((s: IncidentStatus) => s !== Number(status));
      }

      const statusFilterOption = this.state.filterOptions.find((filterOption) => filterOption.name === 'status');
      const statusFilterExist = this.state.filters.some((statusFilter) => statusFilter.name === 'status');

      if (statusFilterExist) {
        this.onFiltersValueChange('status', newStatuses);
      } else {
        this.setState(
          {
            hadInteraction: false,
            filters: [...this.state.filters, statusFilterOption],
          },
          () => {
            this.onFiltersValueChange('status', newStatuses);
          }
        );
      }
    };
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
    return (value: SelectableValue[], items: any[]) => {
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
    const { onChange } = this.props;
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

  onChange = (isOnMount = false) => {
    const { onChange } = this.props;
    const { values } = this.state;

    onChange(values, isOnMount);
  };

  debouncedOnChange = debounce(this.onChange, 500);
}

export default withMobXProviderContext(IncidentsFilters);
