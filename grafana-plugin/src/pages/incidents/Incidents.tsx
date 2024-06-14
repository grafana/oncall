import React, { SyntheticEvent } from 'react';

import { css, cx } from '@emotion/css';
import { GrafanaTheme2, SelectableValue } from '@grafana/data';
import { LabelTag } from '@grafana/labels';
import {
  Button,
  HorizontalGroup,
  Icon,
  LoadingPlaceholder,
  RadioButtonGroup,
  Tooltip,
  VerticalGroup,
  withTheme2,
} from '@grafana/ui';
import { capitalize } from 'lodash-es';
import { observer } from 'mobx-react';
import moment from 'moment-timezone';
import Emoji from 'react-emoji-render';
import { RouteComponentProps, withRouter } from 'react-router-dom';
import { getUtilStyles } from 'styles/utils.styles';

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
import { RemoteFilters, RemoteFiltersState } from 'containers/RemoteFilters/RemoteFilters';
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
import { IncidentRelatedUsers } from 'pages/incident/Incident.helpers';
import { AppFeature } from 'state/features';
import { RootStore } from 'state/rootStore';
import { PageProps, WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import { LocationHelper } from 'utils/LocationHelper';
import { UserActions } from 'utils/authorization/authorization';
import { INCIDENT_HORIZONTAL_SCROLLING_STORAGE, PAGE, PLUGIN_ROOT, TEXT_ELLIPSIS_CLASS } from 'utils/consts';
import { getItem, setItem } from 'utils/localStorage';
import { TableColumn } from 'utils/types';

import { IncidentDropdown } from './parts/IncidentDropdown';
import { SilenceButtonCascader } from './parts/SilenceButtonCascader';

interface Pagination {
  start: number;
  end: number;
}

interface IncidentsPageProps extends WithStoreProps, PageProps, RouteComponentProps {
  theme: GrafanaTheme2;
}

interface IncidentsPageState {
  selectedIncidentIds: Array<ApiSchemas['AlertGroup']['pk']>;
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
      theme,
      store: { alertReceiveChannelStore },
    } = this.props;
    const styles = getStyles(theme);

    return (
      <>
        <div>
          <div className={styles.title}>
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

  renderCards(
    filtersState: RemoteFiltersState,
    filtersSetState: (data: any, callback: () => void) => void,
    filtersOnFiltersValueChange: (status: string, newStatuses: string[]) => void,
    store: RootStore,
    theme: GrafanaTheme2
  ) {
    const { values } = filtersState;
    const { stats } = store.alertGroupStore;

    const status = values.status || [];
    const styles = getStyles(theme);

    return (
      <div className={cx(styles.cards, styles.row)}>
        <div key="new" className={styles.col}>
          <CardButton
            icon={<Icon name="bell" size="xxl" />}
            description="Firing"
            title={stats[IncidentStatus.Firing]}
            selected={status.includes(IncidentStatus.Firing)}
            onClick={this.getStatusButtonClickHandler(
              IncidentStatus.Firing,
              filtersState,
              filtersSetState,
              filtersOnFiltersValueChange
            )}
          />
        </div>
        <div key="acknowledged" className={styles.col}>
          <CardButton
            icon={<Icon name="eye" size="xxl" />}
            description="Acknowledged"
            title={stats[IncidentStatus.Acknowledged]}
            selected={status.includes(IncidentStatus.Acknowledged)}
            onClick={this.getStatusButtonClickHandler(
              IncidentStatus.Acknowledged,
              filtersState,
              filtersSetState,
              filtersOnFiltersValueChange
            )}
          />
        </div>
        <div key="resolved" className={styles.col}>
          <CardButton
            icon={<Icon name="check" size="xxl" />}
            description="Resolved"
            title={stats[IncidentStatus.Resolved]}
            selected={status.includes(IncidentStatus.Resolved)}
            onClick={this.getStatusButtonClickHandler(
              IncidentStatus.Resolved,
              filtersState,
              filtersSetState,
              filtersOnFiltersValueChange
            )}
          />
        </div>
        <div key="silenced" className={styles.col}>
          <CardButton
            icon={<Icon name="bell-slash" size="xxl" />}
            description="Silenced"
            title={stats[IncidentStatus.Silenced]}
            selected={status.includes(IncidentStatus.Silenced)}
            onClick={this.getStatusButtonClickHandler(
              IncidentStatus.Silenced,
              filtersState,
              filtersSetState,
              filtersOnFiltersValueChange
            )}
          />
        </div>
      </div>
    );
  }

  getStatusButtonClickHandler = (
    status: IncidentStatus,
    filtersState: RemoteFiltersState,
    filtersSetState: (data: any, callback: () => void) => void,
    filtersOnFiltersValueChange: (status: string, newStatuses: string[]) => void
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
    const { query, store, theme } = this.props;
    const styles = getStyles(theme);

    return (
      <div className={styles.filters}>
        <RemoteFilters
          query={query}
          page={PAGE.Incidents}
          onChange={this.handleFiltersChange}
          extraFilters={(...args) => {
            return this.renderCards(...args, store, theme);
          }}
          grafanaTeamStore={store.grafanaTeamStore}
          defaultFilters={{
            team: [],
            status: [IncidentStatus.Firing, IncidentStatus.Acknowledged],
            mine: false,
            started_at: 'now-30d_now',
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
    const { selectedIncidentIds, isHorizontalScrolling } = this.state;
    const { store, theme } = this.props;

    if (!store.alertGroupStore.bulkActions) {
      return null;
    }

    const hasSelected = selectedIncidentIds.length > 0;
    const isLoading = LoaderHelper.isLoading(store.loaderStore, [
      ActionKey.FETCH_INCIDENTS,
      ActionKey.FETCH_INCIDENTS_POLLING,
      ActionKey.FETCH_INCIDENTS_AND_STATS,
      ActionKey.INCIDENTS_BULK_UPDATE,
    ]);

    const styles = getStyles(theme);
    const isBulkUpdate = LoaderHelper.isLoading(store.loaderStore, ActionKey.INCIDENTS_BULK_UPDATE);

    return (
      <div className={styles.aboveIncidentsTable}>
        <div className={styles.bulkActionsContainer}>
          <div className={styles.bulkActionsList}>
            {'resolve' in store.alertGroupStore.bulkActions && (
              <WithPermissionControlTooltip key="resolve" userAction={UserActions.AlertGroupsWrite}>
                <Button
                  disabled={!hasSelected || isBulkUpdate}
                  variant="primary"
                  onClick={(ev) => this.onBulkActionClick('resolve', ev)}
                >
                  Resolve
                </Button>
              </WithPermissionControlTooltip>
            )}
            {'acknowledge' in store.alertGroupStore.bulkActions && (
              <WithPermissionControlTooltip key="resolve" userAction={UserActions.AlertGroupsWrite}>
                <Button
                  disabled={!hasSelected || isBulkUpdate}
                  variant="secondary"
                  onClick={(ev) => this.onBulkActionClick('acknowledge', ev)}
                >
                  Acknowledge
                </Button>
              </WithPermissionControlTooltip>
            )}
            {'silence' in store.alertGroupStore.bulkActions && (
              <WithPermissionControlTooltip key="restart" userAction={UserActions.AlertGroupsWrite}>
                <Button
                  disabled={!hasSelected || isBulkUpdate}
                  variant="secondary"
                  onClick={(ev) => this.onBulkActionClick('restart', ev)}
                >
                  Restart
                </Button>
              </WithPermissionControlTooltip>
            )}
            {'restart' in store.alertGroupStore.bulkActions && (
              <WithPermissionControlTooltip key="silence" userAction={UserActions.AlertGroupsWrite}>
                <SilenceButtonCascader
                  disabled={!hasSelected || isBulkUpdate}
                  onSelect={(ev) => this.onBulkActionClick('silence', ev)}
                />
              </WithPermissionControlTooltip>
            )}
            <Text type="secondary">
              {hasSelected
                ? `${selectedIncidentIds.length} Alert Group${selectedIncidentIds.length > 1 ? 's' : ''} selected`
                : 'No Alert Groups selected'}
            </Text>
          </div>

          <div className={styles.fieldsDropdown}>
            <RenderConditionally shouldRender={isLoading}>
              <LoadingPlaceholder text="Loading..." className={styles.loadingPlaceholder} />
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
    const { theme } = this.props;

    const { results, prev, next } = AlertGroupHelper.getAlertSearchResult(alertGroupStore);
    const isLoading =
      LoaderHelper.isLoading(loaderStore, ActionKey.FETCH_INCIDENTS) || filtersStore.options['incidents'] === undefined;

    const styles = getStyles(theme);

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
      <div ref={this.rootElRef}>
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
          <div className={styles.pagination}>
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

  renderId = (record: ApiSchemas['AlertGroup']) => {
    const styles = getUtilStyles(this.props.theme);
    return (
      <TextEllipsisTooltip placement="top" content={`#${record.inside_organization_number}`}>
        <Text type="secondary" className={cx(styles.overflowChild)}>
          #{record.inside_organization_number}
        </Text>
      </TextEllipsisTooltip>
    );
  };

  renderTitle = (record: ApiSchemas['AlertGroup']) => {
    const { store, query } = this.props;
    const { start } = this.state.pagination || {};
    const { incidentsCursor } = store.alertGroupStore;

    return (
      <div>
        <TextEllipsisTooltip placement="top" content={record.render_for_web.title}>
          <Text type="link" size="medium" data-testid="integration-url">
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
      theme,
      store: { alertReceiveChannelStore },
    } = this.props;
    const integration = AlertReceiveChannelHelper.getIntegrationSelectOption(
      alertReceiveChannelStore,
      record.alert_receive_channel
    );
    const utilStyles = getUtilStyles(theme);

    return (
      <TextEllipsisTooltip
        className={cx(utilStyles.flex, utilStyles.flexGapXS)}
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
    if (!item.labels?.length) {
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
        render: (item: ApiSchemas['AlertGroup'], isFull: boolean) => (
          <IncidentRelatedUsers incident={item} isFull={isFull} />
        ),
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

    return async (e: SyntheticEvent) => {
      e.stopPropagation();

      await store.alertGroupStore.doIncidentAction(incidentId, action);
      await store.alertGroupStore.fetchIncidentsAndStats();
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

  onBulkActionClick = async (action: ApiSchemas['AlertGroupBulkActionRequest']['action'], event?: any) => {
    const { selectedIncidentIds } = this.state;
    const { alertGroupStore } = this.props.store;

    const delay = typeof event === 'number' ? event : 0;

    await AlertGroupHelper.updateBulkActionAndRefresh(
      {
        action,
        alert_group_pks: selectedIncidentIds,
        delay,
      },
      alertGroupStore,
      async () => {
        // clear selected incident on finally and update incident stats
        this.setState({ selectedIncidentIds: [] });
        this.setPollingInterval();

        await alertGroupStore.fetchIncidentsAndStats();
      }
    );
  };

  clearPollingInterval() {
    clearInterval(this.pollingIntervalId);
    this.pollingIntervalId = null;
  }

  setPollingInterval() {
    const startPolling = () => {
      this.pollingIntervalId = setTimeout(async () => {
        const isBrowserWindowInactive = document.hidden;
        const { liveUpdatesPaused } = this.props.store.alertGroupStore;

        if (
          !liveUpdatesPaused &&
          !isBrowserWindowInactive &&
          !LoaderHelper.isLoading(this.props.store.loaderStore, [
            ActionKey.FETCH_INCIDENTS,
            ActionKey.FETCH_INCIDENTS_POLLING,
          ])
        ) {
          await this.props.store.alertGroupStore.fetchIncidentsAndStats(true);
        }

        if (this.pollingIntervalId === null) {
          return;
        }

        startPolling();
      }, POLLING_NUM_SECONDS * 1000);
    };

    startPolling();
  }
}

const getStyles = (theme: GrafanaTheme2) => {
  return {
    select: css`
      width: 400px;
    `,

    bau: css`
      ${[1, 2, 3].map(
        (num) => `
      $--line-${num} {
        -webkit-line-clamp: ${num}
      }
    `
      )}
    `,

    actionButtons: css`
      width: 100%;
      justify-content: flex-end;
    `,

    filters: css`
      margin-bottom: 20px;
    `,

    fieldsDropdown: css`
      gap: 8px;
      display: flex;
      margin-left: auto;
      align-items: center;
      padding-left: 4px;
    `,

    aboveIncidentsTable: css`
      display: flex;
      justify-content: space-between;
      align-items: center;
    `,

    horizontalScrollTable: css`
      table td:global(.rc-table-cell) {
        white-space: nowrap;
        padding-right: 16px;
      }
    `,

    bulkActionsContainer: css`
      margin: 10px 0 10px 0;
      display: flex;
      width: 100%;
    `,

    bulkActionsList: css`
      display: flex;
      align-items: center;
      gap: 8px;
    `,

    otherUsers: css`
      color: ${theme.colors.secondary.text};
    `,

    pagination: css`
      width: 100%;
      margin-top: 20px;
    `,

    title: css`
      margin-bottom: 24px;
      right: 0;
    `,

    btnResults: css`
      margin-left: 8px;
    `,

    /* filter cards */

    cards: css`
      margin-top: 25px;
    `,

    row: css`
      display: flex;
      flex-wrap: wrap;
      margin-left: -8px;
      margin-right: -8px;
      row-gap: 16px;
    `,

    loadingPlaceholder: css`
      margin-bottom: 0;
      text-align: center;
    `,

    col: css`
      padding-left: 8px;
      padding-right: 8px;
      display: block;
      flex: 0 0 25%;
      max-width: 25%;

      @media (max-width: 1200px) {
        flex: 0 0 50%;
        max-width: 50%;
      }

      @media (max-width: 800px) {
        flex: 0 0 100%;
        max-width: 100%;
      }
    `,
  };
};

export const IncidentsPage = withRouter(withMobXProviderContext(withTheme2(_IncidentsPage)));
