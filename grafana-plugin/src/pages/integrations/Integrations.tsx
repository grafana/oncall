import React from 'react';

import { HorizontalGroup, Button, VerticalGroup, Icon, ConfirmModal, Tooltip } from '@grafana/ui';
import cn from 'classnames/bind';
import { debounce } from 'lodash-es';
import { observer } from 'mobx-react';
import CopyToClipboard from 'react-copy-to-clipboard';
import Emoji from 'react-emoji-render';
import { RouteComponentProps, withRouter } from 'react-router-dom';

import GTable from 'components/GTable/GTable';
import HamburgerMenu from 'components/HamburgerMenu/HamburgerMenu';
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
import { WithContextMenu } from 'components/WithContextMenu/WithContextMenu';
import IntegrationForm from 'containers/IntegrationForm/IntegrationForm';
import RemoteFilters from 'containers/RemoteFilters/RemoteFilters';
import TeamName from 'containers/TeamName/TeamName';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { HeartIcon, HeartRedIcon } from 'icons';
import { AlertReceiveChannelStore } from 'models/alert_receive_channel/alert_receive_channel';
import { AlertReceiveChannel, MaintenanceMode } from 'models/alert_receive_channel/alert_receive_channel.types';
import IntegrationHelper from 'pages/integration/Integration.helper';
import { PageProps, WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import { openNotification } from 'utils';
import LocationHelper from 'utils/LocationHelper';
import { UserActions } from 'utils/authorization';

import styles from './Integrations.module.scss';

const cx = cn.bind(styles);
const FILTERS_DEBOUNCE_MS = 500;
const ITEMS_PER_PAGE = 15;
const MAX_LINE_LENGTH = 40;

interface IntegrationsState extends PageBaseState {
  integrationsFilters: Filters;
  alertReceiveChannelId?: AlertReceiveChannel['id'] | 'new';
  page: number;
  confirmationModal: {
    isOpen: boolean;
    title: any;
    dismissText: string;
    confirmText: string;
    body?: React.ReactNode;
    description?: string;
    confirmationText?: string;
    onConfirm: () => void;
  };
}

interface IntegrationsProps extends WithStoreProps, PageProps, RouteComponentProps<{ id: string }> {}

@observer
class Integrations extends React.Component<IntegrationsProps, IntegrationsState> {
  state: IntegrationsState = {
    integrationsFilters: { searchTerm: '' },
    errorData: initErrorDataState(),
    page: 1,
    confirmationModal: undefined,
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
    const { alertReceiveChannelId, page, confirmationModal } = this.state;
    const { alertReceiveChannelStore } = store;

    const { count, results } = alertReceiveChannelStore.getPaginatedSearchResult();

    return (
      <>
        <div className={cx('root')}>
          <div className={cx('title')}>
            <HorizontalGroup justify="space-between">
              <VerticalGroup>
                <Text.Title level={3}>Integrations</Text.Title>
                <Text type="secondary">
                  Receive alerts, group and interpret using templates and route to escalations
                </Text>
              </VerticalGroup>
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
              data-testid="integrations-table"
              rowKey="id"
              data={results}
              columns={this.getTableColumns()}
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
            onSubmit={this.update}
            id={alertReceiveChannelId}
          />
        )}

        {confirmationModal && (
          <ConfirmModal
            isOpen={confirmationModal.isOpen}
            title={confirmationModal.title}
            confirmText={confirmationModal.confirmText}
            dismissText="Cancel"
            body={confirmationModal.body}
            description={confirmationModal.description}
            confirmationText={confirmationModal.confirmationText}
            onConfirm={confirmationModal.onConfirm}
            onDismiss={() =>
              this.setState({
                confirmationModal: undefined,
              })
            }
          />
        )}
      </>
    );
  }

  renderNotFound() {
    return (
      <div className={cx('loader')}>
        <Text type="secondary">Not found</Text>
      </div>
    );
  }

  renderName = (item: AlertReceiveChannel) => {
    const {
      query: { p },
    } = this.props;

    return (
      <PluginLink query={{ page: 'integrations', id: item.id, p }}>
        <Text type="link" size="medium">
          <Emoji
            className={cx('title')}
            text={
              item.verbal_name?.length > MAX_LINE_LENGTH
                ? item.verbal_name?.substring(0, MAX_LINE_LENGTH) + '...'
                : item.verbal_name
            }
          />
        </Text>
      </PluginLink>
    );
  };

  renderDatasource(item: AlertReceiveChannel, alertReceiveChannelStore: AlertReceiveChannelStore) {
    const alertReceiveChannel = alertReceiveChannelStore.items[item.id];
    const integration = alertReceiveChannelStore.getIntegration(alertReceiveChannel);
    const isLegacyIntegration = (integration?.value as string)?.toLowerCase().startsWith('legacy_');

    if (isLegacyIntegration) {
      return (
        <HorizontalGroup>
          <Tooltip placement="top" content={'This integration has been deprecated, consider migrating it.'}>
            <Icon name="info-circle" className="u-opacity" />
          </Tooltip>
          <Text type="secondary">
            <span className="u-opacity">{integration?.display_name}</span>
          </Text>
        </HorizontalGroup>
      );
    }

    return (
      <HorizontalGroup>
        <IntegrationLogo scale={0.08} integration={integration} />
        <Text type="secondary">{integration?.display_name}</Text>
      </HorizontalGroup>
    );
  }

  renderIntegrationStatus(item: AlertReceiveChannel, alertReceiveChannelStore: AlertReceiveChannelStore) {
    const alertReceiveChannelCounter = alertReceiveChannelStore.counters[item.id];
    let routesCounter = item.routes_count;
    let connectedEscalationsChainsCount = item.connected_escalations_chains_count;

    return (
      <HorizontalGroup spacing="xs">
        {alertReceiveChannelCounter && (
          <PluginLink query={{ page: 'incidents', integration: item.id }} className={cx('alertsInfoText')}>
            <TooltipBadge
              borderType="primary"
              text={alertReceiveChannelCounter?.alerts_count + '/' + alertReceiveChannelCounter?.alert_groups_count}
              tooltipTitle=""
              tooltipContent={
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
          <TooltipBadge
            borderType="success"
            icon="link"
            text={`${connectedEscalationsChainsCount}/${routesCounter}`}
            tooltipContent={undefined}
            tooltipTitle={
              connectedEscalationsChainsCount +
              ' connected escalation chain' +
              (connectedEscalationsChainsCount === 1 ? '' : 's') +
              ' in ' +
              routesCounter +
              ' route' +
              (routesCounter === 1 ? '' : 's')
            }
          />
        )}
      </HorizontalGroup>
    );
  }

  renderHeartbeat(item: AlertReceiveChannel) {
    const { store } = this.props;
    const { alertReceiveChannelStore, heartbeatStore } = store;
    const alertReceiveChannel = alertReceiveChannelStore.items[item.id];

    const heartbeatId = alertReceiveChannelStore.alertReceiveChannelToHeartbeat[alertReceiveChannel.id];
    const heartbeat = heartbeatStore.items[heartbeatId];

    const heartbeatStatus = Boolean(heartbeat?.status);
    return (
      <div>
        {alertReceiveChannel.is_available_for_integration_heartbeat && heartbeat?.last_heartbeat_time_verbal && (
          <TooltipBadge
            text={undefined}
            className={cx('heartbeat-badge')}
            borderType={heartbeatStatus ? 'success' : 'danger'}
            customIcon={heartbeatStatus ? <HeartIcon /> : <HeartRedIcon />}
            tooltipTitle={`Last heartbeat: ${heartbeat?.last_heartbeat_time_verbal}`}
            tooltipContent={undefined}
          />
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
            tooltipTitle={IntegrationHelper.getMaintenanceText(item.maintenance_till, maintenanceMode)}
            tooltipContent={undefined}
          />
        </div>
      );
    }

    return null;
  }

  renderTeam(item: AlertReceiveChannel, teams: any) {
    return <TeamName team={teams[item.team]} />;
  }

  renderButtons = (item: AlertReceiveChannel) => {
    return (
      <WithContextMenu
        renderMenuItems={() => (
          <div className={cx('integrations-actionsList')}>
            <WithPermissionControlTooltip key="edit" userAction={UserActions.IntegrationsWrite}>
              <div className={cx('integrations-actionItem')} onClick={() => this.onIntegrationEditClick(item.id)}>
                <Text type="primary">Integration settings</Text>
              </div>
            </WithPermissionControlTooltip>

            <CopyToClipboard text={item.id} onCopy={() => openNotification('Integration ID has been copied')}>
              <div className={cx('integrations-actionItem')}>
                <HorizontalGroup spacing={'xs'}>
                  <Icon name="copy" />

                  <Text type="primary">UID: {item.id}</Text>
                </HorizontalGroup>
              </div>
            </CopyToClipboard>

            <div className={cx('thin-line-break')} />

            <WithPermissionControlTooltip key="delete" userAction={UserActions.IntegrationsWrite}>
              <div className={cx('integrations-actionItem')}>
                <div
                  onClick={() => {
                    this.setState({
                      confirmationModal: {
                        isOpen: true,
                        confirmText: 'Delete',
                        dismissText: 'Cancel',
                        onConfirm: () => this.handleDeleteAlertReceiveChannel(item.id),
                        title: 'Delete integration',
                        body: (
                          <Text type="primary">
                            Are you sure you want to delete <Emoji text={item.verbal_name} /> integration?
                          </Text>
                        ),
                      },
                    });
                  }}
                  style={{ width: '100%' }}
                >
                  <Text type="danger">
                    <HorizontalGroup spacing={'xs'}>
                      <Icon name="trash-alt" />
                      <span>Delete Integration</span>
                    </HorizontalGroup>
                  </Text>
                </div>
              </div>
            </WithPermissionControlTooltip>
          </div>
        )}
      >
        {({ openMenu }) => <HamburgerMenu openMenu={openMenu} listBorder={2} listWidth={200} />}
      </WithContextMenu>
    );
  };

  getTableColumns = () => {
    const { grafanaTeamStore, alertReceiveChannelStore } = this.props.store;

    return [
      {
        width: '35%',
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
        width: '20%',
        title: 'Type',
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
        render: (item: AlertReceiveChannel) => this.renderHeartbeat(item),
      },
      {
        width: '15%',
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
  };

  handleChangePage = (page: number) => {
    this.setState({ page }, this.update);
  };

  onIntegrationEditClick = (id: AlertReceiveChannel['id']) => {
    this.setState({ alertReceiveChannelId: id });
  };

  handleDeleteAlertReceiveChannel = (alertReceiveChannelId: AlertReceiveChannel['id']) => {
    const { store } = this.props;

    const { alertReceiveChannelStore } = store;

    alertReceiveChannelStore.deleteAlertReceiveChannel(alertReceiveChannelId).then(this.applyFilters);
    this.setState({ confirmationModal: undefined });
  };

  handleIntegrationsFiltersChange = (integrationsFilters: Filters) => {
    this.setState({ integrationsFilters }, () => this.debouncedUpdateIntegrations());
  };

  applyFilters = () => {
    const { store } = this.props;
    const { alertReceiveChannelStore } = store;
    const { integrationsFilters } = this.state;

    return alertReceiveChannelStore.updatePaginatedItems(integrationsFilters).then(() => {
      this.setState({ page: 1 });
      LocationHelper.update({ p: 1 }, 'partial');
    });
  };

  debouncedUpdateIntegrations = debounce(this.applyFilters, FILTERS_DEBOUNCE_MS);
}

export default withRouter(withMobXProviderContext(Integrations));
