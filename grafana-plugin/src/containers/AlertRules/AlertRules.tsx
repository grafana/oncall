import React, { SyntheticEvent } from 'react';

import {
  Alert,
  Button,
  ConfirmModal,
  Field,
  HorizontalGroup,
  IconButton,
  Input,
  LoadingPlaceholder,
  Modal,
  Tooltip,
} from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import Emoji from 'react-emoji-render';

import Collapse from 'components/Collapse/Collapse';
import Block from 'components/GBlock/Block';
import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import { parseEmojis } from 'containers/AlertRules/AlertRules.helpers';
import { ChatOpsConnectors } from 'containers/AlertRules/parts';
import ChannelFilterForm from 'containers/ChannelFilterForm/ChannelFilterForm';
import EscalationChainForm from 'containers/EscalationChainForm/EscalationChainForm';
import EscalationChainSteps from 'containers/EscalationChainSteps/EscalationChainSteps';
import GSelect from 'containers/GSelect/GSelect';
import { IntegrationSettingsTab } from 'containers/IntegrationSettings/IntegrationSettings.types';
import { WithPermissionControl } from 'containers/WithPermissionControl/WithPermissionControl';
import { AlertReceiveChannel, MaintenanceMode } from 'models/alert_receive_channel/alert_receive_channel.types';
import { ChannelFilter } from 'models/channel_filter/channel_filter.types';
import { EscalationChain } from 'models/escalation_chain/escalation_chain.types';
import { EscalationPolicyOption } from 'models/escalation_policy/escalation_policy.types';
import { MaintenanceType } from 'models/maintenance/maintenance.types';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import { openNotification } from 'utils';
import { isUserActionAllowed, UserActions } from 'utils/authorization';
import sanitize from 'utils/sanitize';

import styles from './AlertRules.module.css';
const cx = cn.bind(styles);

interface AlertRulesProps extends WithStoreProps {
  alertReceiveChannelId: AlertReceiveChannel['id'];
  onDelete: (id: AlertReceiveChannel['id']) => void;
  onEditAlertReceiveChannelTemplates: () => void;
  onShowSettings: (tab?: IntegrationSettingsTab) => void;
}

interface AlertRulesState {
  alertReceiveChannelIdToEditTemplates?: AlertReceiveChannel['id'];
  alertReceiveChannelIdToCreateChannelFilter?: AlertReceiveChannel['id'];
  channelFilterToEdit?: ChannelFilter;
  expandedRoutes: Array<AlertReceiveChannel['id']>;
  settingsVisible?: boolean;
  routeToDelete?: ChannelFilter['id'];
  escalationChainIdToCopy?: EscalationChain['id'];
  channelFilterIdToCopyEscalationChain?: ChannelFilter['id'];
  editIntegrationName?: string;
}

const Notification: React.FC = () => (
  <div>
    Demo alert was generated. Find it on the
    <PluginLink query={{ page: 'incidents' }}> "Alert Groups" </PluginLink>
    page and make sure it didn't freak out your colleagues 😉
  </div>
);

@observer
class AlertRules extends React.Component<AlertRulesProps, AlertRulesState> {
  state: AlertRulesState = {
    expandedRoutes: [],
  };

  newAlertReceiveChannelName?: string;

  componentDidMount() {
    if (this.props.alertReceiveChannelId) {
      this.update();
    }
  }

  componentDidUpdate(prevProps: Readonly<AlertRulesProps>, _prevState: Readonly<AlertRulesState>, _snapshot?: any) {
    if (this.props.alertReceiveChannelId && prevProps.alertReceiveChannelId !== this.props.alertReceiveChannelId) {
      if (prevProps.alertReceiveChannelId) {
        this.setState({
          expandedRoutes: [],
          channelFilterToEdit: undefined,
          channelFilterIdToCopyEscalationChain: undefined,
          alertReceiveChannelIdToCreateChannelFilter: undefined,
          alertReceiveChannelIdToEditTemplates: undefined,
          editIntegrationName: undefined,
        });
      }

      this.update();
    }
  }

  async update() {
    const { store, alertReceiveChannelId } = this.props;
    const { alertReceiveChannelStore, telegramChannelStore } = store;

    store.alertReceiveChannelStore.updateItem(alertReceiveChannelId);

    await store.alertReceiveChannelStore.updateChannelFilters(alertReceiveChannelId);
    await store.escalationChainStore.updateItems();
    await telegramChannelStore.updateTelegramChannels();

    const channelFilterIds = store.alertReceiveChannelStore.channelFilterIds[alertReceiveChannelId];

    store.alertReceiveChannelStore.updateCustomButtons(alertReceiveChannelId);

    const expandedRoutes: Array<ChannelFilter['id']> = [];
    channelFilterIds
      .filter((channelFilterId: ChannelFilter['id']) => {
        const channelFilter = alertReceiveChannelStore.channelFilters[channelFilterId];

        return channelFilter.is_default;
      })
      .forEach((channelFilterId: ChannelFilter['id']) => {
        const channelFilter = alertReceiveChannelStore.channelFilters[channelFilterId];
        store.escalationPolicyStore.updateEscalationPolicies(channelFilter.escalation_chain);

        expandedRoutes.push(channelFilterId);
      });

    this.setState({ expandedRoutes });
  }

  render() {
    const {
      alertReceiveChannelIdToCreateChannelFilter,
      routeToDelete,
      escalationChainIdToCopy,
      channelFilterIdToCopyEscalationChain,
      editIntegrationName,
    } = this.state;
    const { store, alertReceiveChannelId, onShowSettings } = this.props;
    const { alertReceiveChannelStore } = store;

    const alertReceiveChannel = alertReceiveChannelStore.items[alertReceiveChannelId];

    if (!alertReceiveChannel) {
      return <LoadingPlaceholder text="Loading..." />;
    }

    const isIntegrationNameempty = editIntegrationName === '';
    const maintenanceMode = alertReceiveChannel.maintenance_mode;
    return (
      <>
        <div className={cx('root')}>
          <Block className={cx('headerBlock')}>
            <div className={cx('header')}>
              <Text.Title level={4}>
                <HorizontalGroup>
                  Escalate
                  <div className={cx('verbal-name')}>{parseEmojis(alertReceiveChannel?.verbal_name || '')}</div>
                  <Tooltip placement="top" content="Edit name">
                    <IconButton
                      name="pen"
                      onClick={this.getChangeIntegrationNameHandler(parseEmojis(alertReceiveChannel?.verbal_name))}
                    />
                  </Tooltip>
                  alerts
                </HorizontalGroup>
              </Text.Title>

              {editIntegrationName !== undefined && (
                <Modal
                  isOpen
                  title="Edit integration name"
                  onDismiss={() => this.setState({ editIntegrationName: undefined })}
                >
                  <div className={cx('root')}>
                    <Field invalid={isIntegrationNameempty} label="Integration name">
                      <Input
                        autoFocus
                        value={editIntegrationName}
                        onChange={(e: any) => this.setState({ editIntegrationName: e.target.value })}
                      />
                    </Field>
                    <HorizontalGroup>
                      <Button
                        variant="primary"
                        onClick={this.handleChangeAlertReceiveChannelName}
                        disabled={isIntegrationNameempty}
                      >
                        Update
                      </Button>
                      <Button variant="secondary" onClick={() => this.setState({ editIntegrationName: undefined })}>
                        Cancel
                      </Button>
                    </HorizontalGroup>
                  </div>
                </Modal>
              )}
              <div className={cx('buttons')}>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => {
                    onShowSettings(IntegrationSettingsTab.HowToConnect);
                  }}
                >
                  How to connect
                </Button>
                <WithPermissionControl userAction={UserActions.IntegrationsTest}>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={this.getSendDemoAlertClickHandler(alertReceiveChannel.id)}
                  >
                    Send demo alert
                  </Button>
                </WithPermissionControl>
                <div className={cx('icons-container')}>
                  {maintenanceMode === MaintenanceMode.Debug || maintenanceMode === MaintenanceMode.Maintenance ? (
                    <Tooltip placement="top" content="Stop maintenance mode">
                      <Button
                        className="grey-button"
                        disabled={!isUserActionAllowed(UserActions.MaintenanceWrite)}
                        fill="text"
                        icon="square-shape"
                        onClick={this.handleStopMaintenance}
                      />
                    </Tooltip>
                  ) : (
                    <PluginLink
                      query={{
                        page: 'maintenance',
                        maintenance_type: MaintenanceType.alert_receive_channel,
                        alert_receive_channel: alertReceiveChannel.id,
                      }}
                      disabled={!isUserActionAllowed(UserActions.MaintenanceWrite)}
                    >
                      <WithPermissionControl userAction={UserActions.MaintenanceWrite}>
                        <IconButton
                          name="pause"
                          size="sm"
                          tooltip="Setup maintenance mode"
                          tooltipPlacement="top"
                          disabled={!isUserActionAllowed(UserActions.MaintenanceWrite)}
                        />
                      </WithPermissionControl>
                    </PluginLink>
                  )}
                  <IconButton
                    name="cog"
                    size="sm"
                    tooltip="Settings"
                    tooltipPlacement="top"
                    onClick={() => {
                      onShowSettings(IntegrationSettingsTab.Templates);
                    }}
                  />
                  <WithPermissionControl userAction={UserActions.EscalationChainsWrite}>
                    <WithConfirm
                      title="Delete integration?"
                      body={
                        <>
                          Are you sure you want to delete <Emoji text={alertReceiveChannel.verbal_name} /> integration?
                        </>
                      }
                    >
                      <IconButton
                        size="sm"
                        tooltip="Delete"
                        tooltipPlacement="top"
                        onClick={this.handleDeleteAlertReceiveChannel}
                        name="trash-alt"
                      />
                    </WithConfirm>
                  </WithPermissionControl>
                </div>
              </div>
            </div>
          </Block>
          {alertReceiveChannel.description && (
            <div className={cx('description-style')}>
              <Alert
                style={{ marginBottom: '0' }}
                // @ts-ignore
                title={<div dangerouslySetInnerHTML={{ __html: sanitize(alertReceiveChannel.description) }}></div>}
                severity="info"
              />
            </div>
          )}
          <div className={cx('alertRulesContent')}>
            <div className={cx('alertRulesActions')}>
              <Button
                onClick={() => {
                  onShowSettings(IntegrationSettingsTab.Templates);
                }}
                variant="secondary"
              >
                Change alert template and grouping
              </Button>
              {!alertReceiveChannelIdToCreateChannelFilter && (
                <WithPermissionControl userAction={UserActions.IntegrationsWrite}>
                  <Button
                    icon="plus"
                    className={cx('add-new-chain-button', 'TEST-add-new-chain-button')}
                    variant="primary"
                    onClick={this.getCreateChannelFilterClickHandler(alertReceiveChannelId)}
                  >
                    Add Route
                  </Button>
                </WithPermissionControl>
              )}
            </div>
            {alertReceiveChannelIdToCreateChannelFilter && (
              <ChannelFilterForm
                id="new"
                alertReceiveChannelId={alertReceiveChannelIdToCreateChannelFilter}
                onHide={() => {
                  this.setState({
                    alertReceiveChannelIdToCreateChannelFilter: undefined,
                  });
                }}
                onUpdate={this.handleCreateChannelFilter}
              />
            )}
            {routeToDelete && (
              <ConfirmModal
                isOpen
                title="Delete route?"
                body="Are you sure you want to delete this route?"
                confirmText="Delete"
                icon="exclamation-triangle"
                onConfirm={this.handleDeleteRoute}
                onDismiss={() => this.setState({ routeToDelete: undefined })}
              />
            )}
            {channelFilterIdToCopyEscalationChain && (
              <EscalationChainForm
                escalationChainId={escalationChainIdToCopy}
                onHide={() => {
                  this.setState({
                    escalationChainIdToCopy: undefined,
                    channelFilterIdToCopyEscalationChain: undefined,
                  });
                }}
                onUpdate={this.handleEscalationChainCreate}
              />
            )}
            {this.renderRoutes(alertReceiveChannelId)}
          </div>
        </div>
      </>
    );
  }

  getDeleteRouteClickHandler = (routeId: ChannelFilter['id']) => {
    return (event: SyntheticEvent) => {
      event.stopPropagation();
      this.setState({ routeToDelete: routeId });
    };
  };

  handleDeleteRoute = async () => {
    const { routeToDelete } = this.state;
    const { store } = this.props;

    this.setState({ routeToDelete: undefined });

    const { alertReceiveChannelStore } = store;

    await alertReceiveChannelStore.deleteChannelFilter(routeToDelete);

    this.update();
  };

  handleEscalationChainCreate = async (id: EscalationChain['id']) => {
    const { store } = this.props;
    const { alertReceiveChannelStore } = store;
    const { channelFilterIdToCopyEscalationChain } = this.state;

    await alertReceiveChannelStore
      .saveChannelFilter(channelFilterIdToCopyEscalationChain, { escalation_chain: id })
      .then(() => {
        store.escalationPolicyStore.updateEscalationPolicies(id);
      });

    store.escalationChainStore.updateItems();
  };

  handleDeleteAlertReceiveChannel = () => {
    const { alertReceiveChannelId, onDelete } = this.props;
    onDelete(alertReceiveChannelId);
  };

  handleStopMaintenance = () => {
    const { store, alertReceiveChannelId } = this.props;
    const { maintenanceStore, alertReceiveChannelStore } = store;

    maintenanceStore.stopMaintenanceMode(MaintenanceType.alert_receive_channel, alertReceiveChannelId).then(() => {
      alertReceiveChannelStore.updateItem(alertReceiveChannelId);
    });
  };

  getChangeIntegrationNameHandler = (name: string) => {
    return () => {
      this.newAlertReceiveChannelName = name;
      this.setState({ editIntegrationName: name });
    };
  };

  handleChangeAlertReceiveChannelName = () => {
    const { store, alertReceiveChannelId } = this.props;
    const { editIntegrationName } = this.state;

    store.alertReceiveChannelStore
      .saveAlertReceiveChannel(alertReceiveChannelId, { verbal_name: editIntegrationName })
      .then(() => {
        store.alertReceiveChannelStore.updateItem(alertReceiveChannelId);
      });
    this.setState({ editIntegrationName: undefined });
    this.update();
  };

  handleCreateChannelFilter = (id: ChannelFilter['id']) => {
    const { store } = this.props;
    const { alertReceiveChannelIdToCreateChannelFilter, expandedRoutes } = this.state;

    if (!expandedRoutes.includes(id)) {
      this.setState({
        expandedRoutes: [...expandedRoutes, id],
      });
    }

    store.alertReceiveChannelStore.updateChannelFilters(alertReceiveChannelIdToCreateChannelFilter).then(() => {
      const channelFilter = store.alertReceiveChannelStore.channelFilters[id];

      store.escalationPolicyStore.updateEscalationPolicies(channelFilter.escalation_chain);
    });
  };

  getCreateChannelFilterClickHandler = (alertReceiveChannelId: AlertReceiveChannel['id']) => {
    return () => {
      this.setState({
        alertReceiveChannelIdToCreateChannelFilter: alertReceiveChannelId,
      });
    };
  };

  renderRoutes = (alertReceiveChannelId: AlertReceiveChannel['id']) => {
    const { expandedRoutes, channelFilterToEdit } = this.state;
    const { store } = this.props;

    const channelFilterIds = store.alertReceiveChannelStore.channelFilterIds[alertReceiveChannelId];

    if (!channelFilterIds) {
      return <LoadingPlaceholder text="Loading..." />;
    }

    return (
      <div>
        {channelFilterIds.map((channelFilterId: ChannelFilter['id']) => {
          const channelFilter = store.alertReceiveChannelStore.channelFilters[channelFilterId];

          if (channelFilterId === channelFilterToEdit?.id) {
            return (
              <ChannelFilterForm
                key={channelFilterId}
                className={cx('route')}
                id={channelFilterToEdit.id}
                alertReceiveChannelId={channelFilterToEdit.alert_receive_channel}
                data={channelFilterToEdit}
                onHide={() => {
                  this.setState({
                    channelFilterToEdit: undefined,
                  });
                }}
                onUpdate={() => {
                  store.alertReceiveChannelStore.updateChannelFilters(channelFilterToEdit.alert_receive_channel);
                }}
              />
            );
          }

          const escalationChain = store.escalationChainStore.items[channelFilter.escalation_chain];

          let warningAboutModifyingEscalationChain = null;
          const otherRoutes = escalationChain?.number_of_routes - 1;
          const otherIntegrations = escalationChain?.number_of_integrations - 1;

          if (otherRoutes > 0 || otherIntegrations > 0) {
            warningAboutModifyingEscalationChain = (
              <>
                Modifying this will affect{' '}
                {otherRoutes > 0 && (
                  <Text strong>
                    {otherRoutes} other route{otherRoutes === 1 ? '' : 's'}
                  </Text>
                )}
                {otherRoutes > 0 && otherIntegrations > 0 && ' and '}
                {otherIntegrations > 0 && (
                  <Text strong>
                    {otherIntegrations} other integration{otherIntegrations === 1 ? '' : 's'}
                  </Text>
                )}
                .{' '}
              </>
            );
          }

          return (
            <Collapse
              key={channelFilterId}
              collapsible
              className={cx('route')}
              label={this.renderChannelFilterTitle(alertReceiveChannelId, channelFilterId)}
              isOpen={expandedRoutes.includes(channelFilterId)}
              onToggle={this.getChannelFilterToggleHandler(channelFilterId)}
            >
              <div className={cx('route-content')}>
                {escalationChain ? (
                  <>
                    <div className={cx('route-header')}>
                      <Text>
                        <Text strong>
                          <PluginLink query={{ page: 'escalations', id: escalationChain.id }}>
                            {escalationChain?.name}
                          </PluginLink>
                        </Text>{' '}
                        escalation chain
                      </Text>
                      <br />
                      <Text size="small" type="secondary">
                        {warningAboutModifyingEscalationChain}
                        You can{' '}
                        <WithPermissionControl userAction={UserActions.EscalationChainsWrite}>
                          <Button
                            fill="text"
                            size="sm"
                            onClick={() => {
                              this.setState({
                                channelFilterIdToCopyEscalationChain: channelFilterId,
                                escalationChainIdToCopy: escalationChain.id,
                              });
                            }}
                          >
                            Make a copy
                          </Button>
                        </WithPermissionControl>{' '}
                        of the current chain or{' '}
                        <WithPermissionControl userAction={UserActions.EscalationChainsWrite}>
                          <Button
                            fill="text"
                            size="sm"
                            onClick={() => {
                              this.setState({
                                channelFilterIdToCopyEscalationChain: channelFilterId,
                              });
                            }}
                          >
                            Create a new chain
                          </Button>
                        </WithPermissionControl>
                      </Text>
                    </div>
                    {this._renderEscalationPolicies(channelFilter.id)}
                  </>
                ) : (
                  <Text type="secondary">
                    Select Escalation Chain first please ↑ or
                    <Button
                      fill="text"
                      size="sm"
                      onClick={() => {
                        this.setState({
                          channelFilterIdToCopyEscalationChain: channelFilterId,
                        });
                      }}
                    >
                      Create a new
                    </Button>{' '}
                  </Text>
                )}
              </div>
            </Collapse>
          );
        })}
      </div>
    );
  };

  getChannelFilterToggleHandler = (channelFilterId: ChannelFilter['id']) => {
    return (isOpen: boolean) => {
      const { expandedRoutes } = this.state;

      if (!isOpen && expandedRoutes.includes(channelFilterId)) {
        const index = expandedRoutes.indexOf(channelFilterId);
        const newExpandedRoutes = [...expandedRoutes];
        newExpandedRoutes.splice(index, 1);
        this.setState({ expandedRoutes: newExpandedRoutes });
      } else if (isOpen && !expandedRoutes.includes(channelFilterId)) {
        this.setState({ expandedRoutes: [...expandedRoutes, channelFilterId] });
      }
    };
  };

  renderChannelFilterButtons = (channelFilterId: ChannelFilter['id'], index: number) => {
    const { store, alertReceiveChannelId } = this.props;

    const { alertReceiveChannelStore } = store;

    const channelFilterIds = alertReceiveChannelStore.channelFilterIds[alertReceiveChannelId];

    const channelFilter = alertReceiveChannelStore.channelFilters[channelFilterId];

    return (
      <HorizontalGroup spacing="xs">
        {Boolean(index > 0 && !channelFilter.is_default) && (
          <WithPermissionControl userAction={UserActions.IntegrationsWrite}>
            <IconButton
              size="sm"
              name="arrow-up"
              onClick={(e) => {
                e.stopPropagation();
                alertReceiveChannelStore.moveChannelFilterToPosition(alertReceiveChannelId, index, index - 1);
              }}
              tooltip="Move up"
              tooltipPlacement="top"
            />
          </WithPermissionControl>
        )}

        {Boolean(index < channelFilterIds.length - 2 && !channelFilter.is_default) && (
          <WithPermissionControl userAction={UserActions.IntegrationsWrite}>
            <IconButton
              size="sm"
              name="arrow-down"
              onClick={(e) => {
                e.stopPropagation();
                alertReceiveChannelStore.moveChannelFilterToPosition(alertReceiveChannelId, index, index + 1);
              }}
              tooltip="Move down"
              tooltipPlacement="top"
            />
          </WithPermissionControl>
        )}
        {!channelFilter.is_default && (
          <WithPermissionControl userAction={UserActions.IntegrationsWrite}>
            <IconButton
              size="md"
              name="trash-alt"
              onClick={this.getDeleteRouteClickHandler(channelFilter.id)}
              tooltip="Delete"
              tooltipPlacement="top"
            />
          </WithPermissionControl>
        )}
        <WithPermissionControl userAction={UserActions.IntegrationsWrite}>
          <IconButton
            size="md"
            name="pen"
            onClick={(event) => {
              event.stopPropagation();
              this.setState({
                channelFilterToEdit: channelFilter,
              });
            }}
            tooltip="Edit"
            tooltipPlacement="top"
          />
        </WithPermissionControl>
        <WithPermissionControl userAction={UserActions.IntegrationsTest}>
          <Button variant="secondary" size="sm" onClick={this.getSendDemoAlertToParticularRoute(channelFilterId)}>
            Send demo alert
          </Button>
        </WithPermissionControl>
      </HorizontalGroup>
    );
  };

  renderChannelFilterTitle = (
    alertReceiveChannelId: AlertReceiveChannel['id'],
    channelFilterId: ChannelFilter['id']
  ) => {
    const { store } = this.props;
    const channelFilterIds = store.alertReceiveChannelStore.channelFilterIds[alertReceiveChannelId];
    const channelFilter = store.alertReceiveChannelStore.channelFilters[channelFilterId];

    const index = channelFilterIds.indexOf(channelFilterId);
    return (
      <div className={cx('channel-filter-header')}>
        <div className={cx('channel-filter-header-title')}>
          {channelFilter.is_default ? (
            <Text type="success">{channelFilterIds.length > 1 ? 'ELSE ' : ''}</Text>
          ) : (
            <>
              <Text type="success">{index === 0 ? 'IF ' : 'ELSE IF '}</Text>alert payload matches regex
              <Text
                keyboard
                //@ts-ignore
                onClick={this.getEditChannelFilterClickHandler(channelFilter)}
              >
                {channelFilter.filtering_term}
              </Text>
            </>
          )}
          escalate to{' '}
          <WithPermissionControl userAction={UserActions.IntegrationsWrite}>
            <div onClick={(e) => e.stopPropagation()}>
              <GSelect
                showSearch
                modelName="escalationChainStore"
                displayField="name"
                placeholder="Select Escalation Chain"
                className={cx('select', 'control', 'no-trigger-collapse-please')}
                value={channelFilter.escalation_chain}
                onChange={this.getEscalationChainChangeHandler(channelFilterId)}
                showWarningIfEmptyValue={true}
              />
            </div>
          </WithPermissionControl>
        </div>
        <div onClick={(e) => e.stopPropagation()}>{this.renderChannelFilterButtons(channelFilterId, index)}</div>
      </div>
    );
  };

  getEscalationChainChangeHandler = (channelFilterId: ChannelFilter['id']) => {
    const { store } = this.props;
    return (value: EscalationChain['id']) => {
      store.alertReceiveChannelStore
        .saveChannelFilter(channelFilterId, {
          escalation_chain: value,
        })
        .then(() => {
          store.escalationChainStore.updateItems(); // to update number_of_integrations and number_of_routes
          store.escalationPolicyStore.updateEscalationPolicies(value);
        });
    };
  };

  getEditChannelFilterClickHandler = (channelFilter: ChannelFilter) => {
    return (event: MouseEvent) => {
      event.stopPropagation();
      this.setState({
        channelFilterToEdit: channelFilter,
      });
    };
  };

  _renderEscalationPolicies = (channelFilterId: ChannelFilter['id']) => {
    const { store } = this.props;
    const channelFilter = store.alertReceiveChannelStore.channelFilters[channelFilterId];
    const escalationChainId = channelFilter.escalation_chain;

    return (
      <EscalationChainSteps
        addonBefore={<ChatOpsConnectors channelFilterId={channelFilterId} />}
        id={escalationChainId}
      />
    );
  };

  getCreateEscalationPolicyClickHandler = (escalationChainId: EscalationChain['id']) => {
    const { store } = this.props;
    const { escalationPolicyStore } = store;

    return async (option: EscalationPolicyOption) => {
      await escalationPolicyStore.createEscalationPolicy(escalationChainId, {
        step: option.value,
      });

      escalationPolicyStore.updateEscalationPolicies(escalationChainId);
    };
  };

  getEscalationPoliciesSortEndHandler = (escalationChainId: EscalationChain['id']) => {
    const { store } = this.props;
    const { escalationPolicyStore } = store;

    return ({ oldIndex, newIndex }: any) => {
      escalationPolicyStore.moveEscalationPolicyToPosition(oldIndex, newIndex, escalationChainId);
    };
  };

  getSendDemoAlertClickHandler = (id: AlertReceiveChannel['id']) => {
    const {
      store: { alertReceiveChannelStore },
    } = this.props;
    return () => {
      alertReceiveChannelStore.sendDemoAlert(id).then(() => {
        alertReceiveChannelStore.updateCounters();
        openNotification(<Notification />);
      });
    };
  };

  getSendDemoAlertToParticularRoute = (id: ChannelFilter['id']) => {
    const {
      store: { alertReceiveChannelStore },
    } = this.props;
    return () => {
      alertReceiveChannelStore.sendDemoAlertToParticularRoute(id).then(() => {
        openNotification(<Notification />);
      });
    };
  };
}

export default withMobXProviderContext(AlertRules);
