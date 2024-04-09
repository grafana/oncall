import React, { SyntheticEvent } from 'react';

import { SelectableValue } from '@grafana/data';
import { LabelTag } from '@grafana/labels';
import {
  Button,
  HorizontalGroup,
  Icon,
  LoadingPlaceholder,
  RadioButtonGroup,
  Themeable2,
  Tooltip,
  VerticalGroup,
  withTheme2,
} from '@grafana/ui';
import cn from 'classnames/bind';
import { capitalize } from 'lodash-es';
import { observer } from 'mobx-react';
import moment from 'moment-timezone';
import Emoji from 'react-emoji-render';
import { RouteComponentProps, withRouter } from 'react-router-dom';

import { CardButton } from 'components/CardButton/CardButton';
import { CursorPagination } from 'components/CursorPagination/CursorPagination';
import { GTable } from 'components/GTable/GTable';
import { IntegrationLogo } from 'components/IntegrationLogo/IntegrationLogo';
import { ManualAlertGroup } from 'components/ManualAlertGroup/ManualAlertGroup';
import { PluginLink } from 'components/PluginLink/PluginLink';
import { RenderConditionally } from 'components/RenderConditionally/RenderConditionally';
import { Text } from 'components/Text/Text';
import { TextEllipsisTooltip } from 'components/TextEllipsisTooltip/TextEllipsisTooltip';
import { TooltipBadge } from 'components/TooltipBadge/TooltipBadge';
import { Tutorial } from 'components/Tutorial/Tutorial';
import { TutorialStep } from 'components/Tutorial/Tutorial.types';
import { ColumnsSelectorWrapper } from 'containers/ColumnsSelectorWrapper/ColumnsSelectorWrapper';
import { IncidentsFiltersType } from 'containers/IncidentsFilters/IncidentFilters.types';
import { RemoteFilters } from 'containers/RemoteFilters/RemoteFilters';
import { TeamName } from 'containers/TeamName/TeamName';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { AlertReceiveChannelHelper } from 'models/alert_receive_channel/alert_receive_channel.helpers';
import { AlertGroupHelper } from 'models/alertgroup/alertgroup.helpers';
import {
  AlertAction,
  IncidentStatus,
  AlertGroupColumn,
  AlertGroupColumnType,
} from 'models/alertgroup/alertgroup.types';
import { ActionKey } from 'models/loader/action-keys';
import { LoaderHelper } from 'models/loader/loader.helpers';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { renderRelatedUsers } from 'pages/incident/Incident.helpers';
import { AppFeature } from 'state/features';
import { PageProps, WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import { LocationHelper } from 'utils/LocationHelper';
import { UserActions } from 'utils/authorization/authorization';
import { INCIDENT_HORIZONTAL_SCROLLING_STORAGE, PAGE, PLUGIN_ROOT, TEXT_ELLIPSIS_CLASS } from 'utils/consts';
import { getItem, setItem } from 'utils/localStorage';
import { TableColumn } from 'utils/types';

import styles from './Incidents.module.scss';
import { IncidentDropdown } from './parts/IncidentDropdown';
import { SilenceButtonCascader } from './parts/SilenceButtonCascader';

const cx = cn.bind(styles);

interface Pagination {
  start: number;
  end: number;
}

interface IncidentsPageProps extends WithStoreProps, PageProps, RouteComponentProps, Themeable2 {}

interface IncidentsPageState {
  selectedIncidentIds: Array<ApiSchemas['AlertGroup']['pk']>;
  affectedRows: { [key: string]: boolean };
  filters?: Record<string, any>;
  pagination: Pagination;
  showAddAlertGroupForm: boolean;
  isSelectorColumnMenuOpen: boolean;
  isHorizontalScrolling: boolean;
  isFirstIncidentsFetchDone: boolean;
}

const POLLING_NUM_SECONDS = 15;

const PAGINATION_OPTIONS = [
  { label: '25', value: 25 },
  { label: '50', value: 50 },
  { label: '100', value: 100 },
];

const TABLE_SCROLL_OPTIONS: SelectableValue[] = [
  {
    value: false,
    component: () => (
      <Tooltip content="Wrapped columns content">
        <Icon aria-label="Wrap text" name="wrap-text" />
      </Tooltip>
    ),
  },
  {
    value: true,
    component: () => (
      <Tooltip content="One row content with horizontal scrolling">
        <Icon aria-label="One row content" name="arrow-from-right" />
      </Tooltip>
    ),
  },
];

@observer
class _IncidentsPage extends React.Component<IncidentsPageProps, IncidentsPageState> {
  constructor(props: IncidentsPageProps) {
    super(props);

    const {
      store,
      query: { cursor: cursorQuery, start: startQuery, perpage: perpageQuery },
    } = props;

    const start = !isNaN(startQuery) ? Number(startQuery) : 1;
    const pageSize = !isNaN(perpageQuery) ? Number(perpageQuery) : undefined;

    store.alertGroupStore.incidentsCursor = cursorQuery || undefined;

    this.rootElRef = React.createRef<HTMLDivElement>();

    this.state = {
      selectedIncidentIds: [],
      affectedRows: {},
      showAddAlertGroupForm: false,
      pagination: {
        start,
        end: start + pageSize,
      },
      isSelectorColumnMenuOpen: true,
      isHorizontalScrolling: getItem(INCIDENT_HORIZONTAL_SCROLLING_STORAGE) || false,
      isFirstIncidentsFetchDone: false,
    };
  }

  private rootElRef: React.RefObject<HTMLDivElement>;
  private pollingIntervalId: ReturnType<typeof setInterval> = undefined;

  componentDidMount() {
    const { store } = this.props;
    const { alertGroupStore } = store;

    alertGroupStore.fetchBulkActions();
    alertGroupStore.fetchSilenceOptions();

    if (store.hasFeature(AppFeature.Labels)) {
      alertGroupStore.fetchTableSettings();
    }

    this.setPollingInterval();
  }

  componentWillUnmount(): void {
    this.clearPollingInterval();
  }

  render() {
    const { history } = this.props;
    const { showAddAlertGroupForm } = this.state;
    const {
      store: { alertReceiveChannelStore },
    } = this.props;

    return (
      <>
        <div className={cx('root')}>
          <div className={cx('title')}>
            <HorizontalGroup justify="space-between">
              <Text.Title level={3}>Alert Groups</Text.Title>
              <WithPermissionControlTooltip userAction={UserActions.AlertGroupsDirectPaging}>
                <Button icon="plus" onClick={this.handleOnClickEscalateTo}>
                  Escalation
                </Button>
              </WithPermissionControlTooltip>
            </HorizontalGroup>
          </div>
          {this.renderIncidentFilters()}
          {this.renderTable()}
        </div>
        {showAddAlertGroupForm && (
          <ManualAlertGroup
            onHide={() => {
              this.setState({ showAddAlertGroupForm: false });
            }}
            onCreate={(id: ApiSchemas['AlertGroup']['pk']) => {
              history.push(`${PLUGIN_ROOT}/alert-groups/${id}`);
            }}
            alertReceiveChannelStore={alertReceiveChannelStore}
          />
        )}
      </>
    );
  }

  renderCards(filtersState, setFiltersState, filtersOnFiltersValueChange, store) {
    const { values } = filtersState;
    const { stats } = store.alertGroupStore;

    const status = values.status || [];

    return (
      <div className={cx('cards', 'row')}>
        <div key="new" className={cx('col')}>
          <CardButton
            icon={<Icon name="bell" size="xxl" />}
            description="Firing"
            title={stats[IncidentStatus.Firing]}
            selected={status.includes(IncidentStatus.Firing)}
            onClick={this.getStatusButtonClickHandler(
              IncidentStatus.Firing,
              filtersState,
              setFiltersState,
              filtersOnFiltersValueChange
            )}
          />
        </div>
        <div key="acknowledged" className={cx('col')}>
          <CardButton
            icon={<Icon name="eye" size="xxl" />}
            description="Acknowledged"
            title={stats[IncidentStatus.Acknowledged]}
            selected={status.includes(IncidentStatus.Acknowledged)}
            onClick={this.getStatusButtonClickHandler(
              IncidentStatus.Acknowledged,
              filtersState,
              setFiltersState,
              filtersOnFiltersValueChange
            )}
          />
        </div>
        <div key="resolved" className={cx('col')}>
          <CardButton
            icon={<Icon name="check" size="xxl" />}
            description="Resolved"
            title={stats[IncidentStatus.Resolved]}
            selected={status.includes(IncidentStatus.Resolved)}
            onClick={this.getStatusButtonClickHandler(
              IncidentStatus.Resolved,
              filtersState,
              setFiltersState,
              filtersOnFiltersValueChange
            )}
          />
        </div>
        <div key="silenced" className={cx('col')}>
          <CardButton
            icon={<Icon name="bell-slash" size="xxl" />}
            description="Silenced"
            title={stats[IncidentStatus.Silenced]}
            selected={status.includes(IncidentStatus.Silenced)}
            onClick={this.getStatusButtonClickHandler(
              IncidentStatus.Silenced,
              filtersState,
              setFiltersState,
              filtersOnFiltersValueChange
            )}
          />
        </div>
      </div>
    );
  }

  getStatusButtonClickHandler = (
    status: IncidentStatus,
    filtersState,
    filtersSetState,
    filtersOnFiltersValueChange
  ) => {
    return (selected: boolean) => {
      const { values } = filtersState;

      const { status: statusFilter = [] } = values;

      let newStatuses = [...statusFilter];

      if (selected) {
        newStatuses.push(status);
      } else {
        newStatuses = newStatuses.filter((s: IncidentStatus) => s !== Number(status));
      }

      const statusFilterOption = filtersState.filterOptions.find((filterOption) => filterOption.name === 'status');
      const statusFilterExist = filtersState.filters.some((statusFilter) => statusFilter.name === 'status');

      if (statusFilterExist) {
        filtersOnFiltersValueChange('status', newStatuses);
      } else {
        filtersSetState(
          {
            hadInteraction: false,
            filters: [...filtersState.filters, statusFilterOption],
          },
          () => {
            filtersOnFiltersValueChange('status', newStatuses);
          }
        );
      }
    };
  };

  renderIncidentFilters() {
    const { query, store } = this.props;
    const defaultStart = moment().subtract(7, 'days');
    const defaultEnd = moment().add(1, 'days');
    return (
      <div className={cx('filters')}>
        <RemoteFilters
          query={query}
          page={PAGE.Incidents}
          onChange={this.handleFiltersChange}
          extraFilters={(...args) => {
            return this.renderCards(...args, store);
          }}
          grafanaTeamStore={store.grafanaTeamStore}
          defaultFilters={{
            team: [],
            status: [IncidentStatus.Firing, IncidentStatus.Acknowledged],
            mine: false,
            started_at: `${defaultStart.format('YYYY-MM-DDTHH:mm:ss')}/${defaultEnd.format('YYYY-MM-DDTHH:mm:ss')}`,
          }}
        />
      </div>
    );
  }

  handleOnClickEscalateTo = () => {
    this.setState({ showAddAlertGroupForm: true });
  };

  handleFiltersChange = async (filters: IncidentsFiltersType, isOnMount: boolean) => {
    const {
      store: { alertGroupStore },
    } = this.props;

    const { start } = this.state.pagination;

    this.setState({
      filters,
      selectedIncidentIds: [],
      affectedRows: {},
    });

    if (!isOnMount) {
      this.setPagination(1, alertGroupStore.alertsSearchResult.page_size);
    }

    await this.fetchIncidentData(filters);

    if (isOnMount) {
      this.setPagination(start, start + alertGroupStore.alertsSearchResult.page_size - 1);
    }
  };

  setPagination = (start = this.state.pagination?.start, end = this.state.pagination?.end) => {
    this.setState({
      pagination: {
        start,
        end,
      },
    });
  };

  fetchIncidentData = async (filters: IncidentsFiltersType) => {
    const { store } = this.props;
    await store.alertGroupStore.updateIncidentFiltersAndRefetchIncidentsAndStats(
      filters,
      !this.state.isFirstIncidentsFetchDone
    );
    LocationHelper.update({ ...store.alertGroupStore.incidentFilters }, 'partial');
    this.setState({ isFirstIncidentsFetchDone: true });
  };

  onChangeCursor = (cursor: string, direction: 'prev' | 'next') => {
    const { alertGroupStore } = this.props.store;
    const pageSize = alertGroupStore.alertsSearchResult.page_size;

    alertGroupStore.updateIncidentsCursor(cursor);

    this.setState(
      {
        selectedIncidentIds: [],
        pagination: {
          start: this.state.pagination.start + pageSize * (direction === 'prev' ? -1 : 1),
          end: this.state.pagination.end + pageSize * (direction === 'prev' ? -1 : 1),
        },
      },
      () => {
        LocationHelper.update({ start: this.state.pagination.start, perpage: pageSize }, 'partial');
      }
    );
  };

  onEnableHorizontalScroll = (value: boolean) => {
    setItem(INCIDENT_HORIZONTAL_SCROLLING_STORAGE, value);
    this.setState({ isHorizontalScrolling: value });
  };

  handleChangeItemsPerPage = (value: number) => {
    const { store } = this.props;

    store.alertGroupStore.alertsSearchResult = {
      ...store.alertGroupStore.alertsSearchResult,
      page_size: value,
    };

    store.alertGroupStore.setIncidentsItemsPerPage();

    this.setState({
      selectedIncidentIds: [],
      pagination: {
        start: 1,
        end: value,
      },
    });

    LocationHelper.update({ start: 1, perpage: value }, 'partial');
  };

  renderBulkActions = () => {
    const { selectedIncidentIds, affectedRows, isHorizontalScrolling } = this.state;
    const { store } = this.props;

    if (!store.alertGroupStore.bulkActions) {
      return null;
    }

    const { results } = AlertGroupHelper.getAlertSearchResult(store.alertGroupStore);

    const hasSelected = selectedIncidentIds.length > 0;
    const isLoading = LoaderHelper.isLoading(store.loaderStore, ActionKey.FETCH_INCIDENTS);
    const hasInvalidatedAlert = Boolean(
      (results && results.some((alert: ApiSchemas['AlertGroup']) => alert.undoAction)) ||
        Object.keys(affectedRows).length
    );

    return (
      <div className={cx('above-incidents-table')}>
        <div className={cx('bulk-actions-container')}>
          <div className={cx('bulk-actions-list')}>
            {'resolve' in store.alertGroupStore.bulkActions && (
              <WithPermissionControlTooltip key="resolve" userAction={UserActions.AlertGroupsWrite}>
                <Button
                  disabled={!hasSelected}
                  variant="primary"
                  onClick={(ev) => this.getBulkActionClickHandler('resolve', ev)}
                >
                  Resolve
                </Button>
              </WithPermissionControlTooltip>
            )}
            {'acknowledge' in store.alertGroupStore.bulkActions && (
              <WithPermissionControlTooltip key="resolve" userAction={UserActions.AlertGroupsWrite}>
                <Button
                  disabled={!hasSelected}
                  variant="secondary"
                  onClick={(ev) => this.getBulkActionClickHandler('acknowledge', ev)}
                >
                  Acknowledge
                </Button>
              </WithPermissionControlTooltip>
            )}
            {'silence' in store.alertGroupStore.bulkActions && (
              <WithPermissionControlTooltip key="restart" userAction={UserActions.AlertGroupsWrite}>
                <Button
                  disabled={!hasSelected}
                  variant="secondary"
                  onClick={(ev) => this.getBulkActionClickHandler('restart', ev)}
                >
                  Restart
                </Button>
              </WithPermissionControlTooltip>
            )}
            {'restart' in store.alertGroupStore.bulkActions && (
              <WithPermissionControlTooltip key="silence" userAction={UserActions.AlertGroupsWrite}>
                <SilenceButtonCascader
                  disabled={!hasSelected}
                  onSelect={(ev) => this.getBulkActionClickHandler('silence', ev)}
                />
              </WithPermissionControlTooltip>
            )}
            <Text type="secondary">
              {hasSelected
                ? `${selectedIncidentIds.length} Alert Group${selectedIncidentIds.length > 1 ? 's' : ''} selected`
                : 'No Alert Groups selected'}
            </Text>
          </div>

          <div className={cx('fields-dropdown')}>
            <RenderConditionally shouldRender={!isLoading && hasInvalidatedAlert}>
              <HorizontalGroup spacing="xs">
                <Text type="secondary">Results out of date</Text>
                <Button className={cx('btn-results')} variant="primary" onClick={this.onIncidentsUpdateClick}>
                  Refresh
                </Button>
              </HorizontalGroup>
            </RenderConditionally>

            <RenderConditionally shouldRender={isLoading}>
              <LoadingPlaceholder text="Loading..." className={cx('loadingPlaceholder')} />
            </RenderConditionally>

            <RenderConditionally shouldRender={store.hasFeature(AppFeature.Labels)}>
              <RadioButtonGroup
                options={TABLE_SCROLL_OPTIONS}
                value={isHorizontalScrolling}
                onChange={this.onEnableHorizontalScroll}
              />
              <ColumnsSelectorWrapper />
            </RenderConditionally>
          </div>
        </div>
      </div>
    );
  };

  renderTable() {
    const { selectedIncidentIds, pagination, isHorizontalScrolling } = this.state;
    const { alertGroupStore, filtersStore, loaderStore } = this.props.store;

    const { results, prev, next } = AlertGroupHelper.getAlertSearchResult(alertGroupStore);
    const isLoading =
      LoaderHelper.isLoading(loaderStore, ActionKey.FETCH_INCIDENTS) || filtersStore.options['incidents'] === undefined;

    if (results && !results.length) {
      return (
        <Tutorial
          step={TutorialStep.Incidents}
          title={
            <VerticalGroup align="center" spacing="lg">
              <Text type="secondary">
                No alert groups found, review your filter and team settings. Make sure you have at least one working
                integration.
              </Text>
              <PluginLink query={{ page: 'integrations' }}>
                <Button variant="primary" size="lg">
                  Go to integrations page
                </Button>
              </PluginLink>
            </VerticalGroup>
          }
        />
      );
    }

    const tableColumns = this.getTableColumns();

    return (
      <div className={cx('root')} ref={this.rootElRef}>
        {this.renderBulkActions()}
        <GTable
          emptyText={isLoading ? 'Loading...' : 'No alert groups found'}
          className={cx({ 'horizontal-scroll-table': isHorizontalScrolling })}
          rowSelection={{
            selectedRowKeys: selectedIncidentIds,
            onChange: this.handleSelectedIncidentIdsChange,
          }}
          rowKey="pk"
          data={results}
          columns={tableColumns}
          tableLayout="auto"
          scroll={{ x: isHorizontalScrolling ? 'max-content' : undefined }}
        />
        {this.shouldShowPagination() && (
          <div className={cx('pagination')}>
            <CursorPagination
              current={`${pagination.start}-${pagination.end}`}
              itemsPerPage={alertGroupStore.alertsSearchResult?.page_size}
              itemsPerPageOptions={PAGINATION_OPTIONS}
              prev={prev}
              next={next}
              onChange={this.onChangeCursor}
              onChangeItemsPerPage={this.handleChangeItemsPerPage}
            />
          </div>
        )}
      </div>
    );
  }

  renderId(record: ApiSchemas['AlertGroup']) {
    return (
      <TextEllipsisTooltip placement="top" content={`#${record.inside_organization_number}`}>
        <Text type="secondary" className={cx(TEXT_ELLIPSIS_CLASS, 'overflow-child--line-1')}>
          #{record.inside_organization_number}
        </Text>
      </TextEllipsisTooltip>
    );
  }

  renderTitle = (record: ApiSchemas['AlertGroup']) => {
    const { store, query } = this.props;
    const { start } = this.state.pagination || {};
    const { incidentsCursor } = store.alertGroupStore;

    return (
      <div>
        <TextEllipsisTooltip placement="top" content={record.render_for_web.title}>
          <Text type="link" size="medium" className={cx('overflow-parent')} data-testid="integration-url">
            <PluginLink
              query={{
                page: 'alert-groups',
                id: record.pk,
                cursor: incidentsCursor,
                perpage: store.alertGroupStore.alertsSearchResult?.page_size,
                start,
                ...query,
              }}
            >
              <Text className={cx(TEXT_ELLIPSIS_CLASS)}>{record.render_for_web.title}</Text>
            </PluginLink>
          </Text>
        </TextEllipsisTooltip>
        {Boolean(record.dependent_alert_groups.length) && ` + ${record.dependent_alert_groups.length} attached`}
      </div>
    );
  };

  renderAlertsCounter(record: ApiSchemas['AlertGroup']) {
    return <Text type="secondary">{record.alerts_count}</Text>;
  }

  renderSource = (record: ApiSchemas['AlertGroup']) => {
    const {
      store: { alertReceiveChannelStore },
    } = this.props;
    const integration = AlertReceiveChannelHelper.getIntegrationSelectOption(
      alertReceiveChannelStore,
      record.alert_receive_channel
    );

    return (
      <TextEllipsisTooltip
        className={cx('u-flex', 'u-flex-gap-xs', 'overflow-parent')}
        placement="top"
        content={record?.alert_receive_channel?.verbal_name || ''}
      >
        <IntegrationLogo integration={integration} scale={0.1} />
        <Emoji
          className={cx(TEXT_ELLIPSIS_CLASS)}
          text={record.alert_receive_channel?.verbal_name || ''}
          data-testid="integration-name"
        />
      </TextEllipsisTooltip>
    );
  };

  renderStatus = (alert: ApiSchemas['AlertGroup']) => {
    return (
      <IncidentDropdown
        alert={alert}
        onResolve={this.getOnActionButtonClick(alert.pk, AlertAction.Resolve)}
        onUnacknowledge={this.getOnActionButtonClick(alert.pk, AlertAction.unAcknowledge)}
        onUnresolve={this.getOnActionButtonClick(alert.pk, AlertAction.unResolve)}
        onAcknowledge={this.getOnActionButtonClick(alert.pk, AlertAction.Acknowledge)}
        onSilence={this.getSilenceClickHandler(alert)}
        onUnsilence={this.getUnsilenceClickHandler(alert)}
      />
    );
  };

  renderStartedAt = (alert: ApiSchemas['AlertGroup']) => {
    const m = moment(alert.started_at);
    const { isHorizontalScrolling } = this.state;

    const date = m.format('MMM DD, YYYY');
    const time = m.format('HH:mm');

    if (isHorizontalScrolling) {
      // display date as 1 line
      return (
        <Text type="secondary">
          {date} {time}
        </Text>
      );
    }

    return (
      <VerticalGroup spacing="none">
        <Text type="secondary">{date}</Text>
        <Text type="secondary">{time}</Text>
      </VerticalGroup>
    );
  };

  renderLabels = (item: ApiSchemas['AlertGroup']) => {
    if (!item.labels.length) {
      return null;
    }

    return (
      <TooltipBadge
        borderType="secondary"
        icon="tag-alt"
        addPadding
        text={item.labels?.length}
        tooltipContent={
          <VerticalGroup spacing="sm">
            {item.labels.map((label) => (
              <HorizontalGroup spacing="sm" key={label.key.id}>
                <LabelTag label={label.key.name} value={label.value.name} key={label.key.id} />
                <Button
                  size="sm"
                  icon="filter"
                  tooltip="Apply filter"
                  variant="secondary"
                  onClick={this.getApplyLabelFilterClickHandler({
                    // TODO: check with backend
                    key: { ...label.key, prescribed: false },
                    value: { ...label.value, prescribed: false },
                  })}
                />
              </HorizontalGroup>
            ))}
          </VerticalGroup>
        }
      />
    );
  };

  renderTeam(record: ApiSchemas['AlertGroup'], teams: any) {
    return (
      <TextEllipsisTooltip placement="top" content={teams[record.team]?.name}>
        <TeamName className={TEXT_ELLIPSIS_CLASS} team={teams[record.team]} />
      </TextEllipsisTooltip>
    );
  }

  getApplyLabelFilterClickHandler = (label: ApiSchemas['LabelPair']) => {
    const {
      store: { filtersStore },
    } = this.props;

    return () => {
      const {
        filters: { label: oldLabelFilter = [] },
      } = this.state;

      const labelToAddString = `${label.key.id}:${label.value.id}`;
      if (oldLabelFilter.some((label) => label === labelToAddString)) {
        return;
      }

      const newLabelFilter = [...oldLabelFilter, labelToAddString];

      LocationHelper.update({ label: newLabelFilter }, 'partial');

      filtersStore.setNeedToParseFilters(true);
    };
  };

  renderCustomColumn = (column: AlertGroupColumn, alert: ApiSchemas['AlertGroup']) => {
    const matchingLabel = alert.labels?.find((label) => label.key.name === column.name)?.value.name;

    return (
      <TextEllipsisTooltip placement="top" content={matchingLabel}>
        <Text type="secondary" className={cx(TEXT_ELLIPSIS_CLASS, 'overflow-child--line-1')}>
          {matchingLabel}
        </Text>
      </TextEllipsisTooltip>
    );
  };

  shouldShowPagination() {
    const { alertGroupStore } = this.props.store;

    return Boolean(
      this.state.pagination?.start && this.state.pagination?.end && alertGroupStore.alertsSearchResult?.page_size
    );
  }

  handleSelectedIncidentIdsChange = (ids: Array<ApiSchemas['AlertGroup']['pk']>) => {
    this.setState({ selectedIncidentIds: ids }, () => {
      ids.length > 0 ? this.clearPollingInterval() : this.setPollingInterval();
    });
  };

  getTableColumns(): TableColumn[] {
    const { store } = this.props;
    const { isHorizontalScrolling } = this.state;

    const columnMapping: { [key: string]: TableColumn } = {
      ID: {
        title: 'ID',
        key: 'id',
        render: this.renderId,
        width: 150,
      },
      Status: {
        title: 'Status',
        key: 'time',
        render: this.renderStatus,
        width: 140,
      },
      Alerts: {
        title: 'Alerts',
        key: 'alerts',
        render: this.renderAlertsCounter,
        width: 100,
      },
      Integration: {
        title: 'Integration',
        key: 'integration',
        render: this.renderSource,
        grow: 1.7,
      },
      Title: {
        title: 'Title',
        key: 'title',
        render: this.renderTitle,
        className: 'u-max-width-1000',
        grow: 3.5,
      },
      Created: {
        title: 'Created',
        key: 'created',
        render: this.renderStartedAt,
        grow: 1,
      },
      Team: {
        title: 'Team',
        key: 'team',
        render: (item: ApiSchemas['AlertGroup']) => this.renderTeam(item, store.grafanaTeamStore.items),
        grow: 1,
      },
      Users: {
        title: 'Users',
        key: 'users',
        render: renderRelatedUsers,
        grow: 1.5,
      },
    };

    if (store.hasFeature(AppFeature.Labels)) {
      // add labels specific column if enabled
      columnMapping['Labels'] = {
        width: '60px',
        title: 'Labels',
        key: 'labels',
        render: this.renderLabels,
      };
    } else {
      // no filtering needed if we don't have Labels enabled
      return Object.keys(columnMapping).map((col) => columnMapping[col]);
    }

    const visibleColumns = store.alertGroupStore.columns.filter((col) => col.isVisible);
    const visibleColumnsWidth = visibleColumns
      .filter((col) => col.type === AlertGroupColumnType.DEFAULT)
      .reduce((total, current) => {
        const column = columnMapping[current.name];
        return typeof column.width === 'number' ? total + column.width : total;
      }, 0);

    const columnsGrowSum = visibleColumns.reduce((total, current) => {
      const column = columnMapping[current.name];
      return total + (column?.grow || 1);
    }, 0);

    // we set the total width based on the number of columns in the table (200xColCount)
    const totalContainerWidth = isHorizontalScrolling
      ? 200 * visibleColumns.length
      : this.rootElRef?.current?.offsetWidth;
    const remainingContainerWidth = totalContainerWidth - visibleColumnsWidth;

    const mappedColumns: TableColumn[] = store.alertGroupStore.columns
      .filter((col) => col.isVisible)
      .map((column: AlertGroupColumn): TableColumn => {
        // each column has a grow property, simillar to flex-grow
        // and that dictates how much space it should take relative to the other columns
        // we also keep in mind the remaining fixed width columns
        // (such as Status/Alerts which always take up the same amount of space)
        const grow = columnMapping[column.name]?.grow || 1;
        const growWidth = (grow / columnsGrowSum) * remainingContainerWidth;
        const columnWidth = columnMapping[column.name]?.width || growWidth;

        if (column.type === AlertGroupColumnType.DEFAULT && columnMapping[column.name]) {
          return {
            ...columnMapping[column.name],
            width: columnWidth,
          };
        }

        return {
          width: columnWidth,
          title: capitalize(column.name),
          key: column.id,
          render: (item: ApiSchemas['AlertGroup']) => this.renderCustomColumn(column, item),
        };
      });

    return mappedColumns;
  }

  getOnActionButtonClick = (incidentId: string, action: AlertAction): ((e: SyntheticEvent) => Promise<void>) => {
    const { store } = this.props;

    return (e: SyntheticEvent) => {
      e.stopPropagation();

      return store.alertGroupStore.doIncidentAction(incidentId, action);
    };
  };

  getSilenceClickHandler = (alert: ApiSchemas['AlertGroup']): ((value: number) => Promise<void>) => {
    const { store } = this.props;

    return (value: number) => {
      return store.alertGroupStore.doIncidentAction(alert.pk, AlertAction.Silence, value);
    };
  };

  getUnsilenceClickHandler = (alert: ApiSchemas['AlertGroup']): ((event: any) => Promise<void>) => {
    const { store } = this.props;

    return (event: React.SyntheticEvent) => {
      event.stopPropagation();

      return store.alertGroupStore.doIncidentAction(alert.pk, AlertAction.unSilence);
    };
  };

  getBulkActionClickHandler = (action: ApiSchemas['AlertGroupBulkActionRequest']['action'], event?: any) => {
    const { selectedIncidentIds, affectedRows } = this.state;
    const { store } = this.props;

    this.setPollingInterval();

    store.alertGroupStore.setLiveUpdatesPaused(true);
    const delay = typeof event === 'number' ? event : 0;

    this.setState(
      {
        selectedIncidentIds: [],
        affectedRows: selectedIncidentIds.reduce(
          (acc, incidentId: ApiSchemas['AlertGroup']['pk']) => ({
            ...acc,
            [incidentId]: true,
          }),
          affectedRows
        ),
      },
      () => {
        AlertGroupHelper.bulkAction({
          action,
          alert_group_pks: selectedIncidentIds,
          delay,
        });
      }
    );
  };

  onIncidentsUpdateClick = () => {
    const { store } = this.props;

    this.setState({ affectedRows: {} }, () => {
      store.alertGroupStore.fetchIncidentsAndStats();
    });
  };

  clearPollingInterval() {
    clearInterval(this.pollingIntervalId);
    this.pollingIntervalId = null;
  }

  setPollingInterval() {
    const startPolling = (delayed = false) => {
      this.pollingIntervalId = setTimeout(
        async () => {
          const isBrowserWindowInactive = document.hidden;
          if (
            !isBrowserWindowInactive &&
            !LoaderHelper.isLoading(this.props.store.loaderStore, [
              ActionKey.FETCH_INCIDENTS,
              ActionKey.FETCH_INCIDENTS_POLLING,
            ]) &&
            !this.props.store.alertGroupStore.liveUpdatesPaused
          ) {
            await this.props.store.alertGroupStore.fetchIncidentsAndStats(true);
          }

          if (this.pollingIntervalId === null) {
            return;
          }
          startPolling(isBrowserWindowInactive);
        },
        delayed ? 60 * 1000 : POLLING_NUM_SECONDS * 1000
      );
    };

    startPolling();
  }
}

export const IncidentsPage = withRouter(withMobXProviderContext(withTheme2(_IncidentsPage)));
