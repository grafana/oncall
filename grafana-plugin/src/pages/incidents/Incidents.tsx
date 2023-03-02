import React, { ReactElement, SyntheticEvent } from 'react';

import { Button, VerticalGroup, LoadingPlaceholder, HorizontalGroup, Tooltip } from '@grafana/ui';
import cn from 'classnames/bind';
import { get } from 'lodash-es';
import { observer } from 'mobx-react';
import moment from 'moment-timezone';
import Emoji from 'react-emoji-render';
import { RouteComponentProps, withRouter } from 'react-router-dom';

import CursorPagination from 'components/CursorPagination/CursorPagination';
import GTable from 'components/GTable/GTable';
import IntegrationLogo from 'components/IntegrationLogo/IntegrationLogo';
import ManualAlertGroup from 'components/ManualAlertGroup/ManualAlertGroup';
import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import Tutorial from 'components/Tutorial/Tutorial';
import { TutorialStep } from 'components/Tutorial/Tutorial.types';
import { IncidentsFiltersType } from 'containers/IncidentsFilters/IncidentFilters.types';
import IncidentsFilters from 'containers/IncidentsFilters/IncidentsFilters';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { Alert, Alert as AlertType, AlertAction } from 'models/alertgroup/alertgroup.types';
import { renderRelatedUsers } from 'pages/incident/Incident.helpers';
import { PageProps, WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import LocationHelper from 'utils/LocationHelper';
import { UserActions } from 'utils/authorization';
import { PLUGIN_ROOT } from 'utils/consts';

import styles from './Incidents.module.scss';
import { IncidentDropdown } from './parts/IncidentDropdown';
import { SilenceButtonCascader } from './parts/SilenceButtonCascader';

const cx = cn.bind(styles);

interface Pagination {
  start: number;
  end: number;
}

function withSkeleton(fn: (alert: AlertType) => ReactElement | ReactElement[]) {
  const WithSkeleton = (alert: AlertType) => {
    if (alert.short) {
      return <LoadingPlaceholder text={''} />;
    }

    return fn(alert);
  };

  return WithSkeleton;
}

interface IncidentsPageProps extends WithStoreProps, PageProps, RouteComponentProps {}

interface IncidentsPageState {
  selectedIncidentIds: Array<Alert['pk']>;
  affectedRows: { [key: string]: boolean };
  filters?: IncidentsFiltersType;
  pagination: Pagination;
  showAddAlertGroupForm: boolean;
}

const ITEMS_PER_PAGE = 25;
const POLLING_NUM_SECONDS = 15;

@observer
class Incidents extends React.Component<IncidentsPageProps, IncidentsPageState> {
  constructor(props: IncidentsPageProps) {
    super(props);

    const {
      store,
      query: { cursor: cursorQuery, start: startQuery, perpage: perpageQuery },
    } = props;

    const cursor = cursorQuery || undefined;
    const start = !isNaN(startQuery) ? Number(startQuery) : 1;
    const itemsPerPage = !isNaN(perpageQuery) ? Number(perpageQuery) : ITEMS_PER_PAGE;

    store.alertGroupStore.incidentsCursor = cursor;
    store.alertGroupStore.incidentsItemsPerPage = itemsPerPage;

    this.state = {
      selectedIncidentIds: [],
      affectedRows: {},
      showAddAlertGroupForm: false,
      pagination: {
        start,
        end: start + itemsPerPage - 1,
      },
    };

    store.alertGroupStore.updateBulkActions();
    store.alertGroupStore.updateSilenceOptions();
  }

  private pollingIntervalId: NodeJS.Timer = undefined;

  componentWillUnmount(): void {
    this.clearPollingInterval();
  }

  render() {
    const { history } = this.props;
    const { showAddAlertGroupForm } = this.state;
    return (
      <>
        <div className={cx('root')}>
          <div className={cx('title')}>
            <HorizontalGroup justify="space-between">
              <Text.Title level={3}>Alert Groups</Text.Title>
              <WithPermissionControlTooltip userAction={UserActions.AlertGroupsWrite}>
                <Button icon="plus" onClick={this.handleOnClickEscalateTo}>
                  Manual alert group
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
              history.push(`${PLUGIN_ROOT}/incidents/${id}`);
            }}
          />
        )}
      </>
    );
  }

  renderIncidentFilters() {
    const { query } = this.props;

    return (
      <div className={cx('filters')}>
        <IncidentsFilters query={query} onChange={this.handleFiltersChange} />
      </div>
    );
  }

  handleOnClickEscalateTo = () => {
    this.setState({ showAddAlertGroupForm: true });
  };

  handleFiltersChange = (filters: IncidentsFiltersType, isOnMount: boolean) => {
    const { store } = this.props;

    this.setState({
      filters,
      selectedIncidentIds: [],
    });

    if (!isOnMount) {
      this.setState({
        pagination: {
          start: 1,
          end: store.alertGroupStore.incidentsItemsPerPage,
        },
      });
    }

    this.clearPollingInterval();
    this.setPollingInterval(filters, isOnMount);
    this.fetchIncidentData(filters, isOnMount);
  };

  fetchIncidentData = (filters: IncidentsFiltersType, isOnMount: boolean) => {
    const { store } = this.props;
    store.alertGroupStore.updateIncidentFilters(filters, isOnMount); // this line fetches incidents
    LocationHelper.update({ ...store.alertGroupStore.incidentFilters }, 'partial');
  };

  onChangeCursor = (cursor: string, direction: 'prev' | 'next') => {
    const { store } = this.props;

    store.alertGroupStore.updateIncidentsCursor(cursor);

    this.setState(
      {
        selectedIncidentIds: [],
        pagination: {
          start:
            this.state.pagination.start + store.alertGroupStore.incidentsItemsPerPage * (direction === 'prev' ? -1 : 1),
          end:
            this.state.pagination.end + store.alertGroupStore.incidentsItemsPerPage * (direction === 'prev' ? -1 : 1),
        },
      },
      () => {
        LocationHelper.update(
          { start: this.state.pagination.start, perpage: store.alertGroupStore.incidentsItemsPerPage },
          'partial'
        );
      }
    );
  };

  handleChangeItemsPerPage = (value: number) => {
    const { store } = this.props;

    store.alertGroupStore.setIncidentsItemsPerPage(value);

    this.setState({
      selectedIncidentIds: [],
      pagination: {
        start: 1,
        end: store.alertGroupStore.incidentsItemsPerPage,
      },
    });
  };

  renderBulkActions = () => {
    const { selectedIncidentIds, affectedRows } = this.state;
    const { store } = this.props;

    if (!store.alertGroupStore.bulkActions) {
      return null;
    }

    const results = store.alertGroupStore.getAlertSearchResult('default');

    const hasSelected = selectedIncidentIds.length > 0;
    const hasInvalidatedAlert = Boolean(
      (results && results.some((alert: AlertType) => alert.undoAction)) || Object.keys(affectedRows).length
    );

    return (
      <div className={cx('above-incidents-table')}>
        <div className={cx('bulk-actions')}>
          <HorizontalGroup>
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
          </HorizontalGroup>
        </div>
        {hasInvalidatedAlert && (
          <div className={cx('out-of-date')}>
            <Text type="secondary">Results out of date</Text>
            <Button
              style={{ marginLeft: '8px' }}
              disabled={store.alertGroupStore.alertGroupsLoading}
              variant="primary"
              onClick={this.onIncidentsUpdateClick}
            >
              Refresh
            </Button>
          </div>
        )}
      </div>
    );
  };

  renderTable() {
    const { selectedIncidentIds, pagination } = this.state;
    const { store } = this.props;
    const { alertGroupsLoading } = store.alertGroupStore;

    const results = store.alertGroupStore.getAlertSearchResult('default');
    const prev = get(store.alertGroupStore.alertsSearchResult, `default.prev`);
    const next = get(store.alertGroupStore.alertsSearchResult, `default.next`);

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

    const columns = [
      {
        width: '5%',
        title: 'Status',
        key: 'time',
        render: withSkeleton(this.renderStatus),
      },
      {
        width: '10%',
        title: 'ID',
        key: 'id',
        render: withSkeleton(this.renderId),
      },
      {
        width: '35%',
        title: 'Title',
        key: 'title',
        render: withSkeleton(this.renderTitle),
      },
      {
        width: '10%',
        title: 'Alerts',
        key: 'alerts',
        render: withSkeleton(this.renderAlertsCounter),
      },
      {
        width: '15%',
        title: 'Integrations',
        key: 'source',
        render: withSkeleton(this.renderSource),
      },
      {
        width: '10%',
        title: 'Created',
        key: 'created',
        render: withSkeleton(this.renderStartedAt),
      },
      {
        width: '15%',
        title: 'Users',
        key: 'users',
        render: withSkeleton(renderRelatedUsers),
      },
    ];

    return (
      <div className={cx('root')}>
        {this.renderBulkActions()}
        <GTable
          emptyText={alertGroupsLoading ? 'Loading...' : 'No alert groups found'}
          loading={alertGroupsLoading}
          className={cx('incidents-table')}
          rowSelection={{ selectedRowKeys: selectedIncidentIds, onChange: this.handleSelectedIncidentIdsChange }}
          rowKey="pk"
          data={results}
          columns={columns}
        />
        <div className={cx('pagination')}>
          <CursorPagination
            current={`${pagination.start}-${pagination.end}`}
            itemsPerPage={store.alertGroupStore.incidentsItemsPerPage}
            itemsPerPageOptions={[
              { label: '25', value: 25 },
              { label: '50', value: 50 },
              { label: '100', value: 100 },
            ]}
            prev={prev}
            next={next}
            onChange={this.onChangeCursor}
            onChangeItemsPerPage={this.handleChangeItemsPerPage}
          />
        </div>
      </div>
    );
  }

  handleSelectedIncidentIdsChange = (ids: Array<Alert['pk']>) => {
    this.setState({ selectedIncidentIds: ids }, () => {
      ids.length > 0 ? this.clearPollingInterval() : this.setPollingInterval();
    });
  };

  renderId(record: AlertType) {
    return <Text type="secondary">#{record.inside_organization_number}</Text>;
  }

  renderTitle = (record: AlertType) => {
    const { store } = this.props;
    const {
      pagination: { start },
    } = this.state;

    const { incidentsItemsPerPage, incidentsCursor } = store.alertGroupStore;

    return (
      <VerticalGroup spacing="none" justify="center">
        <div className={'table__wrap-column'}>
          <PluginLink
            query={{ page: 'incidents', id: record.pk, cursor: incidentsCursor, perpage: incidentsItemsPerPage, start }}
          >
            <Tooltip placement="top" content={record.render_for_web.title}>
              <span>{record.render_for_web.title}</span>
            </Tooltip>
          </PluginLink>
          {Boolean(record.dependent_alert_groups.length) && ` + ${record.dependent_alert_groups.length} attached`}
        </div>
      </VerticalGroup>
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
      <HorizontalGroup spacing="sm">
        <IntegrationLogo integration={integration} scale={0.1} />
        <Emoji text={record.alert_receive_channel?.verbal_name || ''} />
      </HorizontalGroup>
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

  renderStartedAt(alert: AlertType) {
    const m = moment(alert.started_at);

    return (
      <VerticalGroup spacing="none">
        <Text type="secondary">{m.format('MMM DD, YYYY')}</Text>
        <Text type="secondary">{m.format('hh:mm A')}</Text>
      </VerticalGroup>
    );
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
    this.pollingIntervalId = undefined;
  }

  setPollingInterval(filters: IncidentsFiltersType = this.state.filters, isOnMount = false) {
    this.pollingIntervalId = setInterval(() => {
      this.fetchIncidentData(filters, isOnMount);
    }, POLLING_NUM_SECONDS * 1000);
  }
}

export default withRouter(withMobXProviderContext(Incidents));
