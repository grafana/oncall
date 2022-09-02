import React, { ReactElement, SyntheticEvent } from 'react';

import { AppRootProps } from '@grafana/data';
import { getLocationSrv } from '@grafana/runtime';
import { Button, Icon, Tooltip, VerticalGroup, LoadingPlaceholder, HorizontalGroup } from '@grafana/ui';
import { capitalCase } from 'change-case';
import cn from 'classnames/bind';
import { get } from 'lodash-es';
import { observer } from 'mobx-react';
import moment from 'moment';
import Emoji from 'react-emoji-render';

import CardButton from 'components/CardButton/CardButton';
import CursorPagination from 'components/CursorPagination/CursorPagination';
import GTable from 'components/GTable/GTable';
import IntegrationLogo from 'components/IntegrationLogo/IntegrationLogo';
import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import Tutorial from 'components/Tutorial/Tutorial';
import { TutorialStep } from 'components/Tutorial/Tutorial.types';
import { IncidentsFiltersType } from 'containers/IncidentsFilters/IncidentFilters.types';
import IncidentsFilters from 'containers/IncidentsFilters/IncidentsFilters';
import { WithPermissionControl } from 'containers/WithPermissionControl/WithPermissionControl';
import { MaintenanceIntegration } from 'models/alert_receive_channel';
import { Alert, Alert as AlertType, AlertAction, IncidentStatus } from 'models/alertgroup/alertgroup.types';
import { User } from 'models/user/user.types';
import { getActionButtons, getIncidentStatusTag, renderRelatedUsers } from 'pages/incident/Incident.helpers';
import { move } from 'state/helpers';
import { SelectOption, WithStoreProps } from 'state/types';
import { UserAction } from 'state/userAction';
import { withMobXProviderContext } from 'state/withStore';

import SilenceDropdown from './parts/SilenceDropdown';

import styles from './Incidents.module.css';

const cx = cn.bind(styles);

interface Pagination {
  start: number;
  end: number;
}

function withSkeleton(fn: (alert: AlertType) => ReactElement | ReactElement[]) {
  return (alert: AlertType) => {
    if (alert.short) {
      return <LoadingPlaceholder text={''} />;
    }

    return fn(alert);
  };
}

interface IncidentsPageProps extends WithStoreProps, AppRootProps {}

interface IncidentsPageState {
  selectedIncidentIds: Array<Alert['pk']>;
  affectedRows: { [key: string]: boolean };
  filters?: IncidentsFiltersType;
  pagination: Pagination;
}

const ITEMS_PER_PAGE = 25;

@observer
class Incidents extends React.Component<IncidentsPageProps, IncidentsPageState> {
  constructor(props: IncidentsPageProps) {
    super(props);

    const {
      store,
      query: { id, cursor: cursorQuery, start: startQuery, perpage: perpageQuery },
    } = props;

    const cursor = cursorQuery || undefined;
    const start = !isNaN(startQuery) ? Number(startQuery) : 1;
    const itemsPerPage = !isNaN(perpageQuery) ? Number(perpageQuery) : ITEMS_PER_PAGE;

    store.alertGroupStore.incidentsCursor = cursor;
    store.alertGroupStore.incidentsItemsPerPage = itemsPerPage;

    this.state = {
      selectedIncidentIds: [],
      affectedRows: {},
      pagination: {
        start,
        end: start + itemsPerPage - 1,
      },
    };

    store.alertGroupStore.updateBulkActions();
    store.alertGroupStore.updateSilenceOptions();
  }

  render() {
    return (
      <div className={cx('root')}>
        {this.renderIncidentFilters()}
        {this.renderTable()}
      </div>
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

    store.alertGroupStore.updateIncidentFilters(filters, isOnMount);

    getLocationSrv().update({ query: { page: 'incidents', ...store.alertGroupStore.incidentFilters } });
  };

  onChangeCursor = (cursor: string, direction: 'prev' | 'next') => {
    const { store } = this.props;

    store.alertGroupStore.setIncidentsCursor(cursor);

    this.setState({
      selectedIncidentIds: [],
      pagination: {
        start:
          this.state.pagination.start + store.alertGroupStore.incidentsItemsPerPage * (direction === 'prev' ? -1 : 1),
        end: this.state.pagination.end + store.alertGroupStore.incidentsItemsPerPage * (direction === 'prev' ? -1 : 1),
      },
    });
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
              <WithPermissionControl key="resolve" userAction={UserAction.UpdateIncidents}>
                <Button disabled={!hasSelected} variant="primary" onClick={this.getBulkActionClickHandler('resolve')}>
                  Resolve
                </Button>
              </WithPermissionControl>
            )}
            {'acknowledge' in store.alertGroupStore.bulkActions && (
              <WithPermissionControl key="resolve" userAction={UserAction.UpdateIncidents}>
                <Button
                  disabled={!hasSelected}
                  variant="secondary"
                  onClick={this.getBulkActionClickHandler('acknowledge')}
                >
                  Acknowledge
                </Button>
              </WithPermissionControl>
            )}
            {'silence' in store.alertGroupStore.bulkActions && (
              <WithPermissionControl key="restart" userAction={UserAction.UpdateIncidents}>
                <Button disabled={!hasSelected} variant="secondary" onClick={this.getBulkActionClickHandler('restart')}>
                  Restart
                </Button>
              </WithPermissionControl>
            )}
            {'restart' in store.alertGroupStore.bulkActions && (
              <WithPermissionControl key="silence" userAction={UserAction.UpdateIncidents}>
                <SilenceDropdown disabled={!hasSelected} onSelect={this.getBulkActionClickHandler('silence')} />
              </WithPermissionControl>
            )}

            {/* {store.alertGroupStore.bulkActions.map((bulkAction: SelectOption) => {
            if (bulkAction.value === 'silence') {
              return (
                <SilenceDropdown
                  key="silence"
                  disabled={!hasSelected}
                  style="select"
                  onSelect={this.getBulkActionClickHandler('silence')}
                />
              );
            }

            return (
              <WithPermissionControl key={bulkAction.value} userAction={UserAction.UpdateIncidents}>
                <Button
                  disabled={!hasSelected}
                  icon={actionToIcon[bulkAction.value]}
                  onClick={this.getBulkActionClickHandler(bulkAction.value)}
                >
                  {capitalCase(bulkAction.display_name)}
                </Button>
              </WithPermissionControl>
            );
          })}*/}
            <Text type="secondary">
              {hasSelected
                ? `${selectedIncidentIds.length} alert group${selectedIncidentIds.length > 1 ? 's' : ''} selected`
                : 'No alert groups selected'}
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
    const { selectedIncidentIds, affectedRows, pagination } = this.state;
    const { store } = this.props;
    const {
      teamStore: { currentTeam },
    } = store;
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
        width: '20%',
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
        title: 'Source',
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
      {
        width: '15%',
        key: 'action',
        render: withSkeleton(this.renderActionButtons),
      },
    ];

    const loading = store.alertGroupStore.alertGroupsLoading;

    const hasInvalidatedAlert = Boolean(
      (results && results.some((alert: AlertType) => alert.undoAction)) || Object.keys(affectedRows).length
    );

    return (
      <div className={cx('root')}>
        {this.renderBulkActions()}
        <GTable
          emptyText={alertGroupsLoading ? 'Loading...' : 'No alert groups found'}
          loading={alertGroupsLoading}
          className={cx('incidents-table')}
          rowSelection={{ selectedRowKeys: selectedIncidentIds, onChange: this.handleSelectedIncidentIdsChange }}
          rowKey="pk"
          /*title={() => (
            <Text.Title className={cx('users-title')} level={3}>
              Incidents
            </Text.Title>
          )}*/
          data={results}
          columns={columns}
          // rowClassName={getUserRowClassNameFn(userPkToEdit, userStore.currentUserPk)}
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
    this.setState({ selectedIncidentIds: ids });
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
        <PluginLink
          query={{ page: 'incident', id: record.pk, cursor: incidentsCursor, perpage: incidentsItemsPerPage, start }}
        >
          {record.render_for_web.title}
        </PluginLink>
        {Boolean(record.dependent_alert_groups.length) && `+ ${record.dependent_alert_groups.length} attached`}
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

  renderStatus(record: AlertType) {
    return getIncidentStatusTag(record);
  }

  renderStartedAt(alert: AlertType) {
    const m = moment(alert.started_at);

    return (
      <VerticalGroup spacing="none">
        <Text type="secondary">{m.format('MMM DD, YYYY')}</Text>
        <Text type="secondary">{m.format('hh:mm A')}</Text>
      </VerticalGroup>
    );
  }

  renderRelatedUsers = (record: AlertType) => {
    const { related_users } = record;
    let users = [...related_users];

    function renderUser(user: User, index: number) {
      let badge = undefined;
      if (record.resolved_by_user && user.pk === record.resolved_by_user.pk) {
        badge = <Icon name="check-circle" style={{ color: '#52c41a' }} />;
      } else if (record.acknowledged_by_user && user.pk === record.acknowledged_by_user.pk) {
        badge = <Icon name="eye" style={{ color: '#f2c94c' }} />;
      }

      return (
        <PluginLink query={{ page: 'users', id: user.pk }}>
          <Text type="secondary">
            {index ? ', ' : ''}
            {user.username} {badge}
          </Text>
        </PluginLink>
      );
    }

    if (record.resolved_by_user) {
      const index = users.findIndex((user) => user.pk === record.resolved_by_user.pk);
      if (index > -1) {
        users = move(users, index, 0);
      }
    }

    if (record.acknowledged_by_user) {
      const index = users.findIndex((user) => user.pk === record.acknowledged_by_user.pk);
      if (index > -1) {
        users = move(users, index, 0);
      }
    }

    const visibleUsers = users.slice(0, 2);
    const otherUsers = users.slice(2);

    return (
      <>
        {visibleUsers.map(renderUser)}
        {Boolean(otherUsers.length) && (
          <Tooltip placement="top" content={<>{otherUsers.map(renderUser)}</>}>
            <span className={cx('other-users')}>
              , <span style={{ textDecoration: 'underline' }}>+{otherUsers.length} users</span>{' '}
            </span>
          </Tooltip>
        )}
      </>
    );

    /* if (record.resolved_by_user) {
      const index = users.findIndex((user) => user.pk === record.resolved_by_user.pk);
      if (index > -1) {
        users = move(users, index, 0);
      }
    }

    if (record.acknowledged_by_user) {
      const index = users.findIndex((user) => user.pk === record.acknowledged_by_user.pk);
      if (index > -1) {
        users = move(users, index, 0);
      }
    }

    return (
      <Avatar.Group maxCount={2}>
        {users.map((user: User) => {
          let badge = undefined;
          if (record.resolved_by_user && user.pk === record.resolved_by_user.pk) {
            badge = <CheckCircleOutlined style={{ color: '#52c41a' }} />;
          } else if (record.acknowledged_by_user && user.pk === record.acknowledged_by_user.pk) {
            badge = <EyeOutlined style={{ color: '#f2c94c' }} />;
          }

          return (
            <Tooltip key={user.pk} title={user.username}>
              <Badge count={badge}>
                <PluginLink query={{ page: 'users', id: user.pk }}>
                  <Avatar key={user.pk} src={user.avatar} icon={<UserOutlined />} />
                </PluginLink>
              </Badge>
            </Tooltip>
          );
        })}
      </Avatar.Group>
    ); */
  };

  renderActionButtons = (incident: AlertType) => {
    return getActionButtons(incident, cx, {
      onResolve: this.getOnActionButtonClick(incident.pk, AlertAction.Resolve),
      onUnacknowledge: this.getOnActionButtonClick(incident.pk, AlertAction.unAcknowledge),
      onUnresolve: this.getOnActionButtonClick(incident.pk, AlertAction.unResolve),
      onAcknowledge: this.getOnActionButtonClick(incident.pk, AlertAction.Acknowledge),
      onSilence: this.getSilenceClickHandler(incident),
      onUnsilence: this.getUnsilenceClickHandler(incident),
    });
  };

  getOnActionButtonClick = (incidentId: string, action: AlertAction) => {
    const { store } = this.props;

    return (e: SyntheticEvent) => {
      e.stopPropagation();

      store.alertGroupStore.doIncidentAction(incidentId, action, false);
    };
  };

  getSilenceClickHandler = (alert: AlertType) => {
    const { store } = this.props;

    return (value: number) => {
      store.alertGroupStore.doIncidentAction(alert.pk, AlertAction.Silence, false, {
        delay: value,
      });
    };
  };

  getUnsilenceClickHandler = (alert: AlertType) => {
    const { store } = this.props;
    const { alertGroupStore } = store;

    return (event: any) => {
      event.stopPropagation();

      store.alertGroupStore.doIncidentAction(alert.pk, AlertAction.unSilence, false);
    };
  };

  getBulkActionClickHandler = (action: string | number) => {
    const { selectedIncidentIds, affectedRows } = this.state;
    const { store } = this.props;

    return (event?: any) => {
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
  };

  onIncidentsUpdateClick = () => {
    const { store } = this.props;

    this.setState({ affectedRows: {} }, () => {
      store.alertGroupStore.updateIncidents();
    });
  };
}

export default withMobXProviderContext(Incidents);
