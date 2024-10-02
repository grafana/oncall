import React, { SyntheticEvent } from 'react';

import { css, cx } from '@emotion/css';
import { GrafanaTheme2, durationToMilliseconds, parseDuration, SelectableValue } from '@grafana/data';
import { LabelTag } from '@grafana/labels';
import { Button, Icon, RadioButtonGroup, RefreshPicker, Tooltip, Stack, withTheme2 } from '@grafana/ui';
import { LocationHelper } from 'helpers/LocationHelper';
import { UserActions } from 'helpers/authorization/authorization';
import { INCIDENT_HORIZONTAL_SCROLLING_STORAGE, PAGE, PLUGIN_ROOT, StackSize } from 'helpers/consts';
import { PropsWithRouter, withRouter } from 'helpers/hoc';
import { getItem, setItem } from 'helpers/localStorage';
import { TableColumn } from 'helpers/types';
import { capitalize } from 'lodash-es';
import { observer } from 'mobx-react';
import moment from 'moment-timezone';
import Emoji from 'react-emoji-render';
import { bem, getUtilStyles } from 'styles/utils.styles';

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

import { getIncidentsStyles } from './Incidents.styles';
import { IncidentDropdown } from './parts/IncidentDropdown';
import { SilenceSelect } from './parts/SilenceSelect';

interface Pagination {
  start: number;
  end: number;
}

interface RouteProps {
  id: string;
}

interface IncidentsPageProps extends WithStoreProps, PageProps, PropsWithRouter<RouteProps> {
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
  refreshInterval: string;
}

const PAGINATION_OPTIONS = [
  { label: '25', value: 25 },
  { label: '50', value: 50 },
  { label: '100', value: 100 },
];

const REFRESH_OPTIONS = ['5s', '10s', '15s', '30s', '1m', '5m'];
const REFRESH_DEFAULT_VALUE = '10s';

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
    this.filtersPortalRef = React.createRef<HTMLDivElement>();

    this.state = {
      selectedIncidentIds: [],
      showAddAlertGroupForm: false,
      refreshInterval: REFRESH_DEFAULT_VALUE,
      pagination: {
        start,
        end: start + pageSize,
      },
      isSelectorColumnMenuOpen: true,
      isHorizontalScrolling: getItem(INCIDENT_HORIZONTAL_SCROLLING_STORAGE) || false,
      isFirstIncidentsFetchDone: false,
    };
  }

  private filtersPortalRef: React.RefObject<HTMLDivElement>;
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
    const {
      theme,
      store,
      store: { alertReceiveChannelStore },
      router: { navigate },
    } = this.props;
    const { showAddAlertGroupForm, refreshInterval } = this.state;
    const styles = getIncidentsStyles(theme);

    const isLoading = LoaderHelper.isLoading(store.loaderStore, [
      ActionKey.FETCH_INCIDENTS,
      ActionKey.FETCH_INCIDENTS_POLLING,
      ActionKey.FETCH_INCIDENTS_AND_STATS,
      ActionKey.INCIDENTS_BULK_UPDATE,
    ]);

    return (
      <>
        <div>
          <div className={styles.title}>
            <Stack justifyContent="space-between">
              <Text.Title level={3}>Alert Groups</Text.Title>

              <div className={styles.rightSideFilters}>
                <div ref={this.filtersPortalRef} />
                <RefreshPicker
                  onIntervalChanged={this.onIntervalRefreshChange}
                  onRefresh={this.onRefresh}
                  intervals={REFRESH_OPTIONS}
                  value={refreshInterval}
                  isLoading={isLoading}
                  isOnCanvas
                  showAutoInterval={false}
                />
                <WithPermissionControlTooltip userAction={UserActions.AlertGroupsDirectPaging}>
                  <Button icon="plus" onClick={this.handleOnClickEscalateTo} data-testid="add-escalation-button">
                    Escalation
                  </Button>
                </WithPermissionControlTooltip>
              </div>
            </Stack>
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
              navigate(`${PLUGIN_ROOT}/alert-groups/${id}`);
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
    const styles = getIncidentsStyles(theme);

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
    const styles = getIncidentsStyles(theme);

    return (
      <div className={styles.filters}>
        <RemoteFilters
          query={query}
          page={PAGE.Incidents}
          onChange={this.handleFiltersChange}
          extraInformation={{
            started_at: {
              isClearable: false,
              value: 'now-30d_now',
              portal: this.filtersPortalRef,
              showInputLabel: false,
            },
            team: {
              value: [],
            },
            status: {
              value: [IncidentStatus.Firing, IncidentStatus.Acknowledged],
            },
            mine: {
              value: false,
            },
          }}
          extraFilters={(...args) => {
            return this.renderCards(...args, store, theme);
          }}
          grafanaTeamStore={store.grafanaTeamStore}
        />
      </div>
    );
  }

  onRefresh = async () => {
    this.clearPollingInterval();
    await this.props.store.alertGroupStore.fetchIncidentsAndStats(true);
    this.setPollingInterval();
  };

  onIntervalRefreshChange = (value: string) => {
    this.clearPollingInterval();
    this.setState({ refreshInterval: value }, () => value && this.setPollingInterval());
  };

  handleOnClickEscalateTo = () => {
    this.setState({ showAddAlertGroupForm: true });
  };

  handleFiltersChange = async (filters: IncidentsFiltersType, isOnMount: boolean) => {
    const { alertGroupStore } = this.props.store;
    const { start } = this.state.pagination;

    // Clear polling whenever filters change
    this.clearPollingInterval();

    this.setState({
      filters,
      selectedIncidentIds: [],
    });

    if (!isOnMount) {
      this.setPagination(1, alertGroupStore.alertsSearchResult.page_size);
    }

    try {
      await this.fetchIncidentData(filters);
    } finally {
      // Re-enable polling after query is done
      this.setPollingInterval();
    }

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

    const styles = getIncidentsStyles(theme);
    const hasSelected = selectedIncidentIds.length > 0;
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
                <SilenceSelect
                  disabled={!hasSelected || isBulkUpdate}
                  onSelect={(ev) => this.onBulkActionClick('silence', ev)}
                />
              </WithPermissionControlTooltip>
            )}
            <Text type="secondary" className={styles.alertsSelected}>
              {hasSelected
                ? `${selectedIncidentIds.length} Alert Group${selectedIncidentIds.length > 1 ? 's' : ''} selected`
                : 'No Alert Groups selected'}
            </Text>
          </div>

          <div className={styles.fieldsDropdown}>
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

  renderTable = () => {
    const { selectedIncidentIds, pagination, isHorizontalScrolling } = this.state;
    const { alertGroupStore, filtersStore, loaderStore } = this.props.store;
    const { theme } = this.props;

    const { results, prev, next } = AlertGroupHelper.getAlertSearchResult(alertGroupStore);
    const isLoading =
      LoaderHelper.isLoading(loaderStore, ActionKey.FETCH_INCIDENTS) || filtersStore.options['incidents'] === undefined;

    const styles = getIncidentsStyles(theme);

    if (results && !results.length) {
      return (
        <Tutorial
          step={TutorialStep.Incidents}
          title={
            <Stack direction="column" alignItems="center" gap={StackSize.lg}>
              <Text type="secondary">
                No alert groups found, review your filter and team settings. Make sure you have at least one working
                integration.
              </Text>
              <PluginLink query={{ page: 'integrations' }}>
                <Button variant="primary" size="lg">
                  Go to integrations page
                </Button>
              </PluginLink>
            </Stack>
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
  };

  renderId = (record: ApiSchemas['AlertGroup']) => {
    const styles = getUtilStyles(this.props.theme);
    return (
      <TextEllipsisTooltip placement="top-start" content={`#${record.inside_organization_number}`}>
        <Text type="secondary" className={cx(styles.overflowChild)}>
          #{record.inside_organization_number}
        </Text>
      </TextEllipsisTooltip>
    );
  };

  renderTitle = (record: ApiSchemas['AlertGroup']) => {
    const { store, query, theme } = this.props;
    const { start } = this.state.pagination || {};
    const { incidentsCursor } = store.alertGroupStore;
    const utilStyles = getUtilStyles(theme);

    return (
      <div>
        <TextEllipsisTooltip placement="top-start" content={record.render_for_web.title}>
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
              <Text className={cx(utilStyles.overflowChild)}>{record.render_for_web.title}</Text>
            </PluginLink>
          </Text>
        </TextEllipsisTooltip>
        {Boolean(record.dependent_alert_groups.length) && ` + ${record.dependent_alert_groups.length} attached`}
      </div>
    );
  };

  renderAlertsCounter = (record: ApiSchemas['AlertGroup']) => {
    const { theme } = this.props;
    const utilStyles = getUtilStyles(theme);
    return (
      <Text type="secondary" className={cx(utilStyles.overflowChild, bem(utilStyles.overflowChild, 'line-1'))}>
        {record.alerts_count}
      </Text>
    );
  };

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
        placement="top-start"
        content={record?.alert_receive_channel?.verbal_name || ''}
      >
        <IntegrationLogo integration={integration} scale={0.1} />
        <Emoji
          className={cx(utilStyles.overflowChild)}
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
      <Stack direction="column" gap={StackSize.none} justifyContent="center">
        <Text type="secondary">{date}</Text>
        <Text type="secondary">{time}</Text>
      </Stack>
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
          <Stack direction="column" gap={StackSize.sm}>
            {item.labels.map((label) => (
              <Stack gap={StackSize.sm} key={label.key.id}>
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
              </Stack>
            ))}
          </Stack>
        }
      />
    );
  };

  renderTeam = (record: ApiSchemas['AlertGroup'], teams: any) => {
    const { theme } = this.props;
    const styles = getUtilStyles(theme);

    return (
      <TextEllipsisTooltip placement="top-start" content={teams[record.team]?.name}>
        <TeamName className={styles.overflowChild} team={teams[record.team]} />
      </TextEllipsisTooltip>
    );
  };

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
    const { theme } = this.props;
    const matchingLabel = alert.labels?.find((label) => label.key.name === column.name)?.value.name;
    const utilStyles = getUtilStyles(theme);

    return (
      <TextEllipsisTooltip placement="top-start" content={matchingLabel}>
        <Text type="secondary" className={cx(utilStyles.overflowChild, bem(utilStyles.overflowChild, 'line-1'))}>
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
        width: 100,
      },
      Status: {
        title: 'Status',
        key: 'time',
        render: this.renderStatus,
        width: 110,
      },
      Alerts: {
        title: 'Alerts',
        key: 'alerts',
        render: this.renderAlertsCounter,
        width: 70,
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
        className: css`
          max-width: 1000px;
        `,
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
        grow: 2,
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
      if (!this.state.refreshInterval || this.pollingIntervalId) {
        return;
      }

      const pollingNum = durationToMilliseconds(parseDuration(this.state.refreshInterval));

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

        this.pollingIntervalId = null;
        startPolling();
      }, pollingNum);
    };

    startPolling();
  }
}

export const IncidentsPage = withRouter<RouteProps, Omit<IncidentsPageProps, 'store' | 'meta' | 'theme'>>(
  withMobXProviderContext(withTheme2(_IncidentsPage))
);
