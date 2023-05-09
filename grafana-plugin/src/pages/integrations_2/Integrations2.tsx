import React from 'react';

import { HorizontalGroup, Badge, Tooltip, Button, IconButton } from '@grafana/ui';
import cn from 'classnames/bind';
import { debounce } from 'lodash-es';
import { observer } from 'mobx-react';
import Emoji from 'react-emoji-render';
import { RouteComponentProps, withRouter } from 'react-router-dom';

import GTable from 'components/GTable/GTable';
import IntegrationLogo from 'components/IntegrationLogo/IntegrationLogo';
import { Filters } from 'components/IntegrationsFilters/IntegrationsFilters';
import { PageBaseState } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper';
import {
  getWrongTeamResponseInfo,
  initErrorDataState,
} from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper.helpers';
import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import TooltipBadge from 'components/TooltipBadge/TooltipBadge';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import IntegrationForm from 'containers/IntegrationForm/IntegrationForm';
import RemoteFilters from 'containers/RemoteFilters/RemoteFilters';
import TeamName from 'containers/TeamName/TeamName';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { HeartGreenIcon, HeartRedIcon } from 'icons';
import { AlertReceiveChannel, MaintenanceMode } from 'models/alert_receive_channel';
import IntegrationHelper from 'pages/integration_2/Integration2.helper';
import { PageProps, WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import LocationHelper from 'utils/LocationHelper';
import { UserActions } from 'utils/authorization';

import styles from './Integrations2.module.scss';

const cx = cn.bind(styles);
const FILTERS_DEBOUNCE_MS = 500;
const ITEMS_PER_PAGE = 15;

interface IntegrationsState extends PageBaseState {
  integrationsFilters: Filters;
  alertReceiveChannelId?: AlertReceiveChannel['id'] | 'new';
  page: number;
}

interface IntegrationsProps extends WithStoreProps, PageProps, RouteComponentProps<{ id: string }> {}

@observer
class Integrations extends React.Component<IntegrationsProps, IntegrationsState> {
  state: IntegrationsState = {
    integrationsFilters: { searchTerm: '' },
    errorData: initErrorDataState(),
    page: 1,
  };

  async componentDidMount() {
    const {
      query: { p },
    } = this.props;
    this.setState({ page: p ? Number(p) : 1 }, this.update);

    this.parseQueryParams();
  }

  componentDidUpdate(prevProps: IntegrationsProps) {
    if (prevProps.match.params.id !== this.props.match.params.id) {
      this.parseQueryParams();
    }
  }

  parseQueryParams = async () => {
    this.setState((_prevState) => ({
      errorData: initErrorDataState(),
      alertReceiveChannelId: undefined,
    })); // reset state on query parse

    const {
      store,
      match: {
        params: { id },
      },
    } = this.props;

    if (!id) {
      return;
    }

    let alertReceiveChannel: AlertReceiveChannel | void = undefined;
    const isNewAlertReceiveChannel = id === 'new';

    if (!isNewAlertReceiveChannel) {
      alertReceiveChannel = await store.alertReceiveChannelStore
        .loadItem(id, true)
        .catch((error) => this.setState({ errorData: { ...getWrongTeamResponseInfo(error) } }));
    }

    if (alertReceiveChannel || isNewAlertReceiveChannel) {
      this.setState({ alertReceiveChannelId: id });
    }
  };

  update = () => {
    const { store } = this.props;
    const { page, integrationsFilters } = this.state;
    LocationHelper.update({ p: page }, 'partial');

    return store.alertReceiveChannelStore.updatePaginatedItems(integrationsFilters, page);
  };

  render() {
    const { store, query } = this.props;
    const { alertReceiveChannelId, page } = this.state;
    const { grafanaTeamStore, alertReceiveChannelStore, heartbeatStore } = store;

    const { count, results } = alertReceiveChannelStore.getPaginatedSearchResult();

    const columns = [
      {
        width: '25%',
        title: 'Name',
        key: 'name',
        render: this.renderName,
      },

      {
        width: '15%',
        title: 'Status',
        key: 'status',
        render: (item: AlertReceiveChannel) => this.renderIntegrationStatus(item, alertReceiveChannelStore),
      },
      {
        width: '25%',
        title: 'Datasource',
        key: 'datasource',
        render: (item: AlertReceiveChannel) => this.renderDatasource(item, alertReceiveChannelStore),
      },
      {
        width: '10%',
        title: 'Maintenance',
        key: 'maintenance',
        render: (item: AlertReceiveChannel) => this.renderMaintenance(item),
      },
      {
        width: '5%',
        title: 'Heartbeat',
        key: 'heartbeat',
        render: (item: AlertReceiveChannel) => this.renderHeartbeat(item, alertReceiveChannelStore, heartbeatStore),
      },
      {
        width: '20%',
        title: 'Team',
        render: (item: AlertReceiveChannel) => this.renderTeam(item, grafanaTeamStore.items),
      },
      {
        width: '50px',
        key: 'buttons',
        render: (item: AlertReceiveChannel) => this.renderButtons(item),
        className: cx('buttons'),
      },
    ];

    return (
      <>
        <div className={cx('root')}>
          <div className={cx('title')}>
            <HorizontalGroup justify="space-between">
              <Text.Title level={3}>Integrations 2</Text.Title>
              <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
                <Button
                  onClick={() => {
                    this.setState({ alertReceiveChannelId: 'new' });
                  }}
                  icon="plus"
                  className={cx('newIntegrationButton')}
                >
                  New integration
                </Button>
              </WithPermissionControlTooltip>
            </HorizontalGroup>
          </div>
          <div>
            <RemoteFilters
              query={query}
              page="integrations"
              grafanaTeamStore={store.grafanaTeamStore}
              onChange={this.handleIntegrationsFiltersChange}
            />
            <GTable
              emptyText={this.renderNotFound()}
              rowKey="id"
              data={results}
              columns={columns}
              className={cx('integrations-table')}
              rowClassName={cx('integrations-table-row')}
              pagination={{
                page,
                total: Math.ceil((count || 0) / ITEMS_PER_PAGE),
                onChange: this.handleChangePage,
              }}
            />
          </div>
        </div>
        {alertReceiveChannelId && (
          <IntegrationForm
            onHide={() => {
              this.setState({ alertReceiveChannelId: undefined });
            }}
            onUpdate={this.update}
            id={alertReceiveChannelId}
          />
        )}
      </>
    );
  }

  handleChangePage = (page: number) => {
    this.setState({ page }, this.update);
  };

  renderNotFound() {
    return (
      <div className={cx('loader')}>
        <Text type="secondary">Not found</Text>
      </div>
    );
  }

  renderName(item: AlertReceiveChannel) {
    return (
      <PluginLink query={{ page: 'integrations_2', id: item.id }}>
        <Text type="link" size="medium">
          <Emoji className={cx('title')} text={item.verbal_name} />
        </Text>
      </PluginLink>
    );
  }

  renderDatasource(item: AlertReceiveChannel, alertReceiveChannelStore) {
    const alertReceiveChannel = alertReceiveChannelStore.items[item.id];
    const integration = alertReceiveChannelStore.getIntegration(alertReceiveChannel);
    return (
      <HorizontalGroup spacing="xs">
        <IntegrationLogo scale={0.08} integration={integration} />
        <Text type="secondary" size="small">
          {integration?.display_name}
        </Text>
      </HorizontalGroup>
    );
  }

  renderIntegrationStatus(item: AlertReceiveChannel, alertReceiveChannelStore) {
    const alertReceiveChannelCounter = alertReceiveChannelStore.counters[item.id];
    let routesCounter = item.routes_count;

    return (
      <HorizontalGroup spacing="xs">
        {alertReceiveChannelCounter && (
          <PluginLink query={{ page: 'incidents', integration: item.id }} className={cx('alertsInfoText')}>
            <Badge
              text={alertReceiveChannelCounter?.alerts_count + '/' + alertReceiveChannelCounter?.alert_groups_count}
              color={'blue'}
              tooltip={
                alertReceiveChannelCounter?.alerts_count +
                ' alert' +
                (alertReceiveChannelCounter?.alerts_count === 1 ? '' : 's') +
                ' in ' +
                alertReceiveChannelCounter?.alert_groups_count +
                ' alert group' +
                (alertReceiveChannelCounter?.alert_groups_count === 1 ? '' : 's')
              }
            />
          </PluginLink>
        )}
        {routesCounter && (
          <Badge icon="link" text={routesCounter} color={'green'} tooltip={`${routesCounter} routes`} />
        )}
      </HorizontalGroup>
    );
  }

  renderHeartbeat(item: AlertReceiveChannel, alertReceiveChannelStore, heartbeatStore) {
    const alertReceiveChannel = alertReceiveChannelStore.items[item.id];

    const heartbeatId = alertReceiveChannelStore.alertReceiveChannelToHeartbeat[alertReceiveChannel.id];
    const heartbeat = heartbeatStore.items[heartbeatId];

    const heartbeatStatus = Boolean(heartbeat?.status);
    return (
      <div className={cx('heartbeat')}>
        {alertReceiveChannel.is_available_for_integration_heartbeat && (
          <Tooltip
            placement="top"
            content={
              heartbeat
                ? `Last heartbeat: ${heartbeat.last_heartbeat_time_verbal || 'never'}`
                : 'Click to setup heartbeat'
            }
          >
            <div className={cx('heartbeat-icon')} onClick={() => {}}>
              {heartbeatStatus ? <HeartGreenIcon /> : <HeartRedIcon />}
            </div>
          </Tooltip>
        )}
      </div>
    );
  }

  renderMaintenance(item: AlertReceiveChannel) {
    const maintenanceMode = item.maintenance_mode;

    if (maintenanceMode === MaintenanceMode.Debug || maintenanceMode === MaintenanceMode.Maintenance) {
      return (
        <div className={cx('u-flex')}>
          <TooltipBadge
            borderType="primary"
            icon="pause"
            text={IntegrationHelper.getMaintenanceText(item.maintenance_till)}
            tooltipTitle={IntegrationHelper.getMaintenanceText(item.maintenance_till, item.maintenance_mode)}
            tooltipContent={undefined}
          />
        </div>
      );
    }

    return null;
  }

  // handleStopMaintenance = (item: AlertReceiveChannel, maintenanceStore, alertReceiveChannelStore) => {
  //   maintenanceStore.stopMaintenanceMode(MaintenanceType.alert_receive_channel, item.id).then(() => {
  //     alertReceiveChannelStore.updateItem(item.id);
  //   });
  // };

  renderTeam(item: AlertReceiveChannel, teams: any) {
    return <TeamName team={teams[item.team]} />;
  }

  renderButtons = (item: AlertReceiveChannel) => {
    return (
      <HorizontalGroup justify="flex-end">
        <WithPermissionControlTooltip key="edit" userAction={UserActions.IntegrationsWrite}>
          <IconButton tooltip="Settings" name="cog" onClick={() => this.onIntegrationEditClick(item.id)} />
        </WithPermissionControlTooltip>
        <WithPermissionControlTooltip key="edit" userAction={UserActions.IntegrationsWrite}>
          <WithConfirm>
            <IconButton
              tooltip="Delete"
              name="trash-alt"
              onClick={() => this.handleDeleteAlertReceiveChannel(item.id)}
            />
          </WithConfirm>
        </WithPermissionControlTooltip>
      </HorizontalGroup>
    );
  };

  onIntegrationEditClick = (id: AlertReceiveChannel['id']) => {
    this.setState({ alertReceiveChannelId: id });
  };

  handleDeleteAlertReceiveChannel = (alertReceiveChannelId: AlertReceiveChannel['id']) => {
    const { store } = this.props;

    const { alertReceiveChannelStore } = store;

    alertReceiveChannelStore.deleteAlertReceiveChannel(alertReceiveChannelId).then(this.applyFilters);
  };

  handleIntegrationsFiltersChange = (integrationsFilters: Filters) => {
    this.setState({ integrationsFilters }, () => this.debouncedUpdateIntegrations());
  };

  applyFilters = () => {
    const { store } = this.props;
    const { alertReceiveChannelStore } = store;
    const { integrationsFilters } = this.state;

    return alertReceiveChannelStore.updateItems(integrationsFilters);
  };

  debouncedUpdateIntegrations = debounce(this.applyFilters, FILTERS_DEBOUNCE_MS);
}

export default withRouter(withMobXProviderContext(Integrations));
