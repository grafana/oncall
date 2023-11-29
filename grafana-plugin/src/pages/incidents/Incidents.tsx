import React, { SyntheticEvent } from 'react';

import { LabelTag } from '@grafana/labels';
import { Button, HorizontalGroup, Icon, RadioButtonGroup, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { capitalize } from 'lodash-es';
import { observer } from 'mobx-react';
import moment from 'moment-timezone';
import Emoji from 'react-emoji-render';
import { RouteComponentProps, withRouter } from 'react-router-dom';

import CardButton from 'components/CardButton/CardButton';
import CursorPagination from 'components/CursorPagination/CursorPagination';
import GTable from 'components/GTable/GTable';
import IntegrationLogo from 'components/IntegrationLogo/IntegrationLogo';
import ManualAlertGroup from 'components/ManualAlertGroup/ManualAlertGroup';
import PluginLink from 'components/PluginLink/PluginLink';
import RenderConditionally from 'components/RenderConditionally/RenderConditionally';
import Text from 'components/Text/Text';
import TextEllipsisTooltip from 'components/TextEllipsisTooltip/TextEllipsisTooltip';
import TooltipBadge from 'components/TooltipBadge/TooltipBadge';
import Tutorial from 'components/Tutorial/Tutorial';
import { TutorialStep } from 'components/Tutorial/Tutorial.types';
import ColumnsSelectorWrapper from 'containers/ColumnsSelectorWrapper/ColumnsSelectorWrapper';
import { IncidentsFiltersType } from 'containers/IncidentsFilters/IncidentFilters.types';
import RemoteFilters from 'containers/RemoteFilters/RemoteFilters';
import TeamName from 'containers/TeamName/TeamName';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import {
  Alert,
  Alert as AlertType,
  AlertAction,
  IncidentStatus,
  AlertGroupColumn,
  AlertGroupColumnType,
} from 'models/alertgroup/alertgroup.types';
import { LabelKeyValue } from 'models/label/label.types';
import { renderRelatedUsers } from 'pages/incident/Incident.helpers';
import { AppFeature } from 'state/features';
import { PageProps, WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import LocationHelper from 'utils/LocationHelper';
import { UserActions } from 'utils/authorization';
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
interface IncidentsPageProps extends WithStoreProps, PageProps, RouteComponentProps {}

interface IncidentsPageState {
  selectedIncidentIds: Array<Alert['pk']>;
  affectedRows: { [key: string]: boolean };
  filters?: Record<string, any>;
  pagination: Pagination;
  showAddAlertGroupForm: boolean;
  isSelectorColumnMenuOpen: boolean;
  isHorizontalScrolling: boolean;
}

const POLLING_NUM_SECONDS = 15;

const PAGINATION_OPTIONS = [
  { label: '25', value: 25 },
  { label: '50', value: 50 },
  { label: '100', value: 100 },
];

const TABLE_SCROLL_OPTIONS: Array<{ value: boolean; icon: string }> = [
  { value: false, icon: 'wrap-text' },
  {
    value: true,
    icon: 'arrow-from-right',
  },
];

@observer
class Incidents extends React.Component<IncidentsPageProps, IncidentsPageState> {
  constructor(props: IncidentsPageProps) {
    super(props);

    const {
      store,
      query: { cursor: cursorQuery, start: startQuery, perpage: perpageQuery },
    } = props;

    const start = !isNaN(startQuery) ? Number(startQuery) : 1;
    const pageSize = !isNaN(perpageQuery) ? Number(perpageQuery) : undefined;

    store.alertGroupStore.incidentsCursor = cursorQuery || undefined;

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
    };
  }

  private pollingIntervalId: NodeJS.Timer = undefined;

  componentDidMount() {
    const { store } = this.props;
    const { alertGroupStore } = store;

    alertGroupStore.updateBulkActions();
    alertGroupStore.updateSilenceOptions();

    if (store.hasFeature(AppFeature.Labels)) {
      alertGroupStore.fetchTableSettings();
    }
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
            onCreate={(id: Alert['pk']) => {
              history.push(`${PLUGIN_ROOT}/alert-groups/${id}`);
            }}
            alertReceiveChannelStore={alertReceiveChannelStore}
          />
        )}
      </>
    );
  }

  renderCards(filtersState, setFiltersState, filtersOnFiltersValueChange) {
    const { store } = this.props;

    const { values } = filtersState;

    const { newIncidents, acknowledgedIncidents, resolvedIncidents, silencedIncidents } = store.alertGroupStore;

    const { count: newIncidentsCount } = newIncidents;
    const { count: acknowledgedIncidentsCount } = acknowledgedIncidents;
    const { count: resolvedIncidentsCount } = resolvedIncidents;
    const { count: silencedIncidentsCount } = silencedIncidents;

    const status = values.status || [];

    return (
      <div className={cx('cards', 'row')}>
        <div key="new" className={cx('col')}>
          <CardButton
            icon={<Icon name="bell" size="xxl" />}
            description="Firing"
            title={newIncidentsCount}
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
            title={acknowledgedIncidentsCount}
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
            title={resolvedIncidentsCount}
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
            title={silencedIncidentsCount}
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
    return (
      <div className={cx('filters')}>
        <RemoteFilters
          query={query}
          page={PAGE.Incidents}
          onChange={this.handleFiltersChange}
          extraFilters={this.renderCards.bind(this)}
          grafanaTeamStore={store.grafanaTeamStore}
          defaultFilters={{
            team: [],
            status: [IncidentStatus.Firing, IncidentStatus.Acknowledged],
            mine: false,
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
    });

    if (!isOnMount) {
      this.setPagination(1, alertGroupStore.alertsSearchResult['default'].page_size);
    }

    this.clearPollingInterval();
    this.setPollingInterval(filters, isOnMount);

    await this.fetchIncidentData(filters, isOnMount);

    if (isOnMount) {
      this.setPagination(start, start + alertGroupStore.alertsSearchResult['default'].page_size - 1);
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

  fetchIncidentData = async (filters: IncidentsFiltersType, isOnMount: boolean) => {
    const { store } = this.props;
    await store.alertGroupStore.updateIncidentFilters(filters, isOnMount); // this line fetches the incidents
    LocationHelper.update({ ...store.alertGroupStore.incidentFilters }, 'partial');
  };

  onChangeCursor = (cursor: string, direction: 'prev' | 'next') => {
    const { alertGroupStore } = this.props.store;
    const pageSize = alertGroupStore.alertsSearchResult['default'].page_size;

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

    store.alertGroupStore.alertsSearchResult['default'] = {
      ...store.alertGroupStore.alertsSearchResult['default'],
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

    const { results } = store.alertGroupStore.getAlertSearchResult('default');

    const hasSelected = selectedIncidentIds.length > 0;
    const hasInvalidatedAlert = Boolean(
      (results && results.some((alert: AlertType) => alert.undoAction)) || Object.keys(affectedRows).length
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
            <RenderConditionally shouldRender={hasInvalidatedAlert}>
              <HorizontalGroup spacing="xs">
                <Text type="secondary">Results out of date</Text>
                <Button
                  className={cx('btn-results')}
                  disabled={store.alertGroupStore.alertGroupsLoading}
                  variant="primary"
                  onClick={this.onIncidentsUpdateClick}
                >
                  Refresh
                </Button>
              </HorizontalGroup>
            </RenderConditionally>

            <RenderConditionally shouldRender={store.hasFeature(AppFeature.Labels)}>
              <RadioButtonGroup
                options={TABLE_SCROLL_OPTIONS}
                value={isHorizontalScrolling}
                onChange={this.onEnableHorizontalScroll}
              />
            </RenderConditionally>

            <RenderConditionally shouldRender={store.hasFeature(AppFeature.Labels)}>
              <ColumnsSelectorWrapper />
            </RenderConditionally>
          </div>
        </div>
      </div>
    );
  };

  renderTable() {
    const { selectedIncidentIds, pagination, isHorizontalScrolling } = this.state;
    const { alertGroupStore, filtersStore } = this.props.store;

    const { results, prev, next } = alertGroupStore.getAlertSearchResult('default');
    const isLoading = alertGroupStore.alertGroupsLoading || filtersStore.options['incidents'] === undefined;

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
      <div className={cx('root')}>
        {this.renderBulkActions()}
        <GTable
          emptyText={isLoading ? 'Loading...' : 'No alert groups found'}
          loading={isLoading}
          className={cx('incidents-table')}
          rowSelection={{
            selectedRowKeys: selectedIncidentIds,
            onChange: this.handleSelectedIncidentIdsChange,
          }}
          rowKey="pk"
          data={results}
          columns={tableColumns}
          tableLayout="auto"
          scroll={{ x: isHorizontalScrolling ? `${Math.max(2000, tableColumns.length * 250)}px` : true }}
        />
        {this.shouldShowPagination() && (
          <div className={cx('pagination')}>
            <CursorPagination
              current={`${pagination.start}-${pagination.end}`}
              itemsPerPage={alertGroupStore.alertsSearchResult?.['default']?.page_size}
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

  renderId(record: AlertType) {
    return (
      <TextEllipsisTooltip placement="top" content={`#${record.inside_organization_number}`}>
        <Text type="secondary" className={cx(TEXT_ELLIPSIS_CLASS, 'overflow-child--line-1')}>
          #{record.inside_organization_number}
        </Text>
      </TextEllipsisTooltip>
    );
  }

  renderTitle = (record: AlertType) => {
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
                perpage: store.alertGroupStore.alertsSearchResult?.['default']?.page_size,
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

  renderAlertsCounter(record: AlertType) {
    return <Text type="secondary">{record.alerts_count}</Text>;
  }

  renderSource = (record: AlertType) => {
    const {
      store: { alertReceiveChannelStore },
    } = this.props;
    const integration = alertReceiveChannelStore.getIntegration(record.alert_receive_channel);

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

  renderStatus = (alert: AlertType) => {
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

  renderStartedAt = (alert: AlertType) => {
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

  renderLabels = (item: AlertType) => {
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
                  onClick={this.getApplyLabelFilterClickHandler(label)}
                />
              </HorizontalGroup>
            ))}
          </VerticalGroup>
        }
      />
    );
  };

  renderTeam(record: AlertType, teams: any) {
    return (
      <TextEllipsisTooltip placement="top" content={teams[record.team]?.name}>
        <TeamName className={TEXT_ELLIPSIS_CLASS} team={teams[record.team]} />
      </TextEllipsisTooltip>
    );
  }

  getApplyLabelFilterClickHandler = (label: LabelKeyValue) => {
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

  renderCustomColumn = (column: AlertGroupColumn, alert: AlertType) => {
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
      this.state.pagination?.start &&
        this.state.pagination?.end &&
        alertGroupStore.alertsSearchResult?.['default']?.page_size
    );
  }

  handleSelectedIncidentIdsChange = (ids: Array<Alert['pk']>) => {
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
        width: isHorizontalScrolling ? '100px' : '10%',
      },
      Status: {
        title: 'Status',
        key: 'time',
        render: this.renderStatus,
        width: '140px',
      },
      Alerts: {
        title: 'Alerts',
        key: 'alerts',
        render: this.renderAlertsCounter,
        width: '100px',
      },
      Integration: {
        title: 'Integration',
        key: 'integration',
        render: this.renderSource,
        width: isHorizontalScrolling ? undefined : '15%',
      },
      Title: {
        title: 'Title',
        key: 'title',
        render: this.renderTitle,
        width: isHorizontalScrolling ? undefined : '35%',
      },
      Created: {
        title: 'Created',
        key: 'created',
        render: this.renderStartedAt,
        width: isHorizontalScrolling ? undefined : '10%',
      },
      Team: {
        title: 'Team',
        key: 'team',
        render: (item: AlertType) => this.renderTeam(item, store.grafanaTeamStore.items),
        width: isHorizontalScrolling ? undefined : '10%',
      },
      Users: {
        title: 'Users',
        key: 'users',
        render: renderRelatedUsers,
        width: isHorizontalScrolling ? undefined : '15%',
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

    const mappedColumns: TableColumn[] = store.alertGroupStore.columns
      .filter((col) => col.isVisible)
      .map((column: AlertGroupColumn): TableColumn => {
        if (column.type === AlertGroupColumnType.DEFAULT && columnMapping[column.name]) {
          return columnMapping[column.name];
        }

        return {
          width: isHorizontalScrolling ? '200px' : '10%',
          title: capitalize(column.name),
          key: column.id,
          render: (item: AlertType) => this.renderCustomColumn(column, item),
        };
      });

    return mappedColumns;
  }

  getOnActionButtonClick = (incidentId: string, action: AlertAction): ((e: SyntheticEvent) => Promise<void>) => {
    const { store } = this.props;

    return (e: SyntheticEvent) => {
      e.stopPropagation();

      return store.alertGroupStore.doIncidentAction(incidentId, action, false);
    };
  };

  getSilenceClickHandler = (alert: AlertType): ((value: number) => Promise<void>) => {
    const { store } = this.props;

    return (value: number) => {
      return store.alertGroupStore.doIncidentAction(alert.pk, AlertAction.Silence, false, {
        delay: value,
      });
    };
  };

  getUnsilenceClickHandler = (alert: AlertType): ((event: any) => Promise<void>) => {
    const { store } = this.props;

    return (event: React.SyntheticEvent) => {
      event.stopPropagation();

      return store.alertGroupStore.doIncidentAction(alert.pk, AlertAction.unSilence, false);
    };
  };

  getBulkActionClickHandler = (action: string | number, event?: any) => {
    const { selectedIncidentIds, affectedRows } = this.state;
    const { store } = this.props;

    this.setPollingInterval();

    store.alertGroupStore.liveUpdatesPaused = true;
    const delay = typeof event === 'number' ? event : 0;

    this.setState(
      {
        selectedIncidentIds: [],
        affectedRows: selectedIncidentIds.reduce(
          (acc, incidentId: AlertType['pk']) => ({
            ...acc,
            [incidentId]: true,
          }),
          affectedRows
        ),
      },
      () => {
        store.alertGroupStore.bulkAction({
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
      store.alertGroupStore.updateIncidents();
    });
  };

  clearPollingInterval() {
    clearInterval(this.pollingIntervalId);
    this.pollingIntervalId = null;
  }

  setPollingInterval(filters: IncidentsFiltersType = this.state.filters, isOnMount = false) {
    const startPolling = (delayed = false) => {
      this.pollingIntervalId = setTimeout(
        async () => {
          const isBrowserWindowInactive = document.hidden;
          if (!isBrowserWindowInactive) {
            await this.fetchIncidentData(filters, isOnMount);
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

export default withRouter(withMobXProviderContext(Incidents));
