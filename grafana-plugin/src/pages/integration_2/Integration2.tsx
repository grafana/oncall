import React, { useRef } from 'react';

import {
  Button,
  HorizontalGroup,
  VerticalGroup,
  Icon,
  LoadingPlaceholder,
  Tooltip,
  Modal,
  CascaderOption,
  IconButton,
} from '@grafana/ui';
import cn from 'classnames/bind';
import { get } from 'lodash-es';
import { observer } from 'mobx-react';
import CopyToClipboard from 'react-copy-to-clipboard';
import Emoji from 'react-emoji-render';
import { RouteComponentProps, withRouter } from 'react-router-dom';

import { TemplateForEdit, templateForEdit } from 'components/AlertTemplates/AlertTemplatesForm.config';
import IntegrationCollapsibleTreeView, {
  IntegrationCollapsibleItem,
} from 'components/IntegrationCollapsibleTreeView/IntegrationCollapsibleTreeView';
import IntegrationLogo from 'components/IntegrationLogo/IntegrationLogo';
import IntegrationMaskedInputField from 'components/IntegrationMaskedInputField/IntegrationMaskedInputField';
import PageErrorHandlingWrapper, { PageBaseState } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper';
import { initErrorDataState } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper.helpers';
import PluginLink from 'components/PluginLink/PluginLink';
import SourceCode from 'components/SourceCode/SourceCode';
import Tag from 'components/Tag/Tag';
import Text from 'components/Text/Text';
import TooltipBadge from 'components/TooltipBadge/TooltipBadge';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import { WithContextMenu } from 'components/WithContextMenu/WithContextMenu';
import EditRegexpRouteTemplateModal from 'containers/EditRegexpRouteTemplateModal/EditRegexpRouteTemplateModal';
import IntegrationTemplate from 'containers/IntegrationTemplate/IntegrationTemplate';
import TeamName from 'containers/TeamName/TeamName';
import UserDisplayWithAvatar from 'containers/UserDisplay/UserDisplayWithAvatar';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { HeartGreenIcon, HeartRedIcon } from 'icons';
import { AlertReceiveChannel } from 'models/alert_receive_channel';
import { ChannelFilter } from 'models/channel_filter';
import { PageProps, WithStoreProps } from 'state/types';
import { useStore } from 'state/useStore';
import { withMobXProviderContext } from 'state/withStore';
import { openNotification, openErrorNotification } from 'utils';
import { getVar } from 'utils/DOM';
import LocationHelper from 'utils/LocationHelper';
import { UserActions } from 'utils/authorization';
import { DATASOURCE_ALERTING, PLUGIN_ROOT } from 'utils/consts';

import CollapsedIntegrationRouteDisplay from './CollapsedIntegrationRouteDisplay';
import ExpandedIntegrationRouteDisplay from './ExpandedIntegrationRouteDisplay';
import { INTEGRATION_DEMO_PAYLOAD, INTEGRATION_TEMPLATES_LIST } from './Integration2.config';
import IntegrationHelper from './Integration2.helper';
import styles from './Integration2.module.scss';
import IntegrationBlock from './IntegrationBlock';
import IntegrationTemplateList from './IntegrationTemplatesList';

const cx = cn.bind(styles);

interface Integration2Props extends WithStoreProps, PageProps, RouteComponentProps<{ id: string }> {}

interface Integration2State extends PageBaseState {
  isDemoModalOpen: boolean;
  isEditTemplateModalOpen: boolean;
  selectedTemplate: TemplateForEdit;
  isEditRegexpRouteTemplateModalOpen: boolean;
  channelFilterIdForEdit: ChannelFilter['id'];
  isNewRoute: boolean;
}

// This can be further improved by using a ref instead
const ACTIONS_LIST_WIDTH = 160;
const ACTIONS_LIST_BORDER = 2;

@observer
class Integration2 extends React.Component<Integration2Props, Integration2State> {
  constructor(props: Integration2Props) {
    super(props);

    this.state = {
      errorData: initErrorDataState(),
      isDemoModalOpen: false,
      isEditTemplateModalOpen: false,
      selectedTemplate: undefined,
      isEditRegexpRouteTemplateModalOpen: false,
      channelFilterIdForEdit: undefined,
      isNewRoute: false,
    };
  }

  async componentDidMount() {
    const {
      match: {
        params: { id },
      },
      query,
    } = this.props;
    const {
      store: { alertReceiveChannelStore },
    } = this.props;

    if (query?.template) {
      this.openEditTemplateModal(query.template, query.routeId && query.routeId);
    }
    await Promise.all([this.loadIntegration(), alertReceiveChannelStore.updateTemplates(id)]);
  }

  render() {
    const {
      errorData,
      isDemoModalOpen,
      isEditTemplateModalOpen,
      selectedTemplate,
      isEditRegexpRouteTemplateModalOpen,
      channelFilterIdForEdit,
      isNewRoute,
    } = this.state;
    const {
      store: { alertReceiveChannelStore, grafanaTeamStore },
      match: {
        params: { id },
      },
    } = this.props;

    const { isNotFoundError, isWrongTeamError } = errorData;

    const alertReceiveChannel = alertReceiveChannelStore.items[id];
    const channelFilterIds = alertReceiveChannelStore.channelFilterIds[id];
    const templates = alertReceiveChannelStore.templates[id];

    if ((!alertReceiveChannel && !isNotFoundError && !isWrongTeamError) || !channelFilterIds || !templates) {
      return (
        <div className={cx('root')}>
          <LoadingPlaceholder text="Loading Integration..." />
        </div>
      );
    }

    const integration = alertReceiveChannelStore.getIntegration(alertReceiveChannel);
    const alertReceiveChannelCounter = alertReceiveChannelStore.counters[id];

    return (
      <PageErrorHandlingWrapper errorData={errorData} objectName="integration" pageName="Integration">
        {() => (
          <div className={cx('root')}>
            <div className={cx('integration__heading-container')}>
              <PluginLink query={{ page: 'integrations_2' }}>
                <IconButton name="arrow-left" size="xxl" />
              </PluginLink>
              <h1 className={cx('integration__name')}>
                <Emoji text={alertReceiveChannel.verbal_name} />
              </h1>

              <div className={cx('integration__actions')}>
                <WithPermissionControlTooltip userAction={UserActions.IntegrationsTest}>
                  <Button
                    variant="secondary"
                    size="md"
                    onClick={() => this.setState({ isDemoModalOpen: true })}
                    data-testid="send-demo-alert"
                  >
                    Send demo alert
                  </Button>
                </WithPermissionControlTooltip>

                <WithContextMenu
                  renderMenuItems={({ closeMenu }) => (
                    <div className={cx('integration__actionsList')} id="integration-menu-options">
                      <div
                        className={cx('integration__actionItem')}
                        onClick={() => this.openIntegrationSettings(id, closeMenu)}
                      >
                        <Text type="primary">Integration Settings</Text>
                      </div>

                      <div className={cx('integration__actionItem')} onClick={() => this.openHearbeat(id, closeMenu)}>
                        Hearbeat
                      </div>

                      <div
                        className={cx('integration__actionItem')}
                        onClick={() => this.openStartMaintenance(id, closeMenu)}
                      >
                        <Text type="primary">Start Maintenance</Text>
                      </div>

                      <div className="thin-line-break" />

                      <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
                        <div className={cx('integration__actionItem')}>
                          <WithConfirm
                            title="Delete integration?"
                            body={
                              <>
                                Are you sure you want to delete <Emoji text={alertReceiveChannel.verbal_name} />{' '}
                                integration?
                              </>
                            }
                          >
                            <div onClick={() => this.deleteIntegration(id, closeMenu)}>
                              <div
                                onClick={() => {
                                  // work-around to prevent 2 modals showing (withContextMenu and ConfirmModal)
                                  const contextMenuEl =
                                    document.querySelector<HTMLElement>('#integration-menu-options');
                                  if (contextMenuEl) {
                                    contextMenuEl.style.display = 'none';
                                  }
                                }}
                              >
                                <Text type="danger">Stop Maintenance</Text>
                              </div>
                            </div>
                          </WithConfirm>
                        </div>
                      </WithPermissionControlTooltip>
                    </div>
                  )}
                >
                  {({ openMenu }) => <HamburgerMenu openMenu={openMenu} />}
                </WithContextMenu>
              </div>
            </div>

            <div className={cx('integration__subheading-container')}>
              {alertReceiveChannel.description_short && (
                <Text type="secondary" className={cx('integration__description')}>
                  {alertReceiveChannel.description_short}
                </Text>
              )}
              <HorizontalGroup>
                {alertReceiveChannelCounter && (
                  <TooltipBadge
                    borderType="primary"
                    tooltipTitle={undefined}
                    tooltipContent={this.getAlertReceiveChannelCounterTooltip()}
                    text={
                      alertReceiveChannelCounter?.alerts_count + '/' + alertReceiveChannelCounter?.alert_groups_count
                    }
                  />
                )}

                <TooltipBadge
                  borderType="success"
                  icon="link"
                  text={channelFilterIds.length}
                  tooltipTitle={`${channelFilterIds.length} Routes`}
                  tooltipContent={undefined}
                />

                {alertReceiveChannel.maintenance_till && (
                  <TooltipBadge
                    borderType="primary"
                    icon="pause"
                    text={IntegrationHelper.getMaintenanceText(alertReceiveChannel.maintenance_till)}
                    tooltipTitle={IntegrationHelper.getMaintenanceText(
                      alertReceiveChannel.maintenance_till,
                      alertReceiveChannel.maintenance_mode
                    )}
                    tooltipContent={undefined}
                  />
                )}

                {this.renderHearbeat(alertReceiveChannel)}

                <HorizontalGroup spacing="xs">
                  <Text type="secondary">Type:</Text>
                  <HorizontalGroup spacing="none">
                    <IntegrationLogo scale={0.08} integration={integration} />
                    <Text type="secondary" size="small">
                      {integration?.display_name}
                    </Text>
                  </HorizontalGroup>
                </HorizontalGroup>
                <HorizontalGroup spacing="xs">
                  <Text type="secondary">Team:</Text>
                  <TeamName team={grafanaTeamStore.items[alertReceiveChannel.team]} size="small" />
                </HorizontalGroup>
                <HorizontalGroup spacing="xs">
                  <Text type="secondary">Created by:</Text>
                  <UserDisplayWithAvatar id={alertReceiveChannel.author as any}></UserDisplayWithAvatar>
                </HorizontalGroup>
              </HorizontalGroup>
            </div>

            <IntegrationCollapsibleTreeView
              configElements={[
                {
                  isCollapsible: false,
                  customIcon: 'plug',
                  collapsedView: null,
                  expandedView: <HowToConnectComponent id={id} />,
                },
                {
                  isExpanded: false,
                  isCollapsible: true,
                  collapsedView: (
                    <IntegrationBlock
                      hasCollapsedBorder
                      heading={
                        <HorizontalGroup spacing={'md'}>
                          <Tag color={getVar('--tag-secondary')} className={cx('tag')}>
                            <Text type="primary" size="small">
                              Templates
                            </Text>
                          </Tag>

                          <HorizontalGroup spacing={'xs'}>
                            <Text type="secondary">Grouping:</Text>
                            <Text type="link">
                              {IntegrationHelper.truncateLine(templates['grouping_id_template'] || '')}
                            </Text>
                          </HorizontalGroup>

                          <HorizontalGroup spacing={'xs'}>
                            <Text type="secondary">Autoresolve:</Text>
                            <Text type="link">
                              {IntegrationHelper.truncateLine(templates['resolve_condition_template'] || '')}
                            </Text>
                          </HorizontalGroup>

                          <HorizontalGroup spacing={'xs'}>
                            <Text type="secondary">Visualisation:</Text>
                            <Text type="primary">Multiple</Text>
                          </HorizontalGroup>
                        </HorizontalGroup>
                      }
                      content={null}
                    />
                  ),
                  expandedView: (
                    <IntegrationBlock
                      hasCollapsedBorder
                      heading={
                        <HorizontalGroup>
                          <Tag color={getVar('--tag-secondary')} className={cx('tag')}>
                            <Text type="primary" size="small">
                              Templates
                            </Text>
                          </Tag>
                        </HorizontalGroup>
                      }
                      content={
                        <IntegrationTemplateList
                          getTemplatesList={this.getTemplatesList}
                          openEditTemplateModal={this.openEditTemplateModal}
                          templates={templates}
                        />
                      }
                    />
                  ),
                },
                {
                  customIcon: 'plus',
                  isCollapsible: false,
                  collapsedView: null,
                  expandedView: (
                    <div className={cx('routesSection')}>
                      <VerticalGroup spacing="md">
                        <Text type={'primary'}>Routes</Text>
                        <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
                          <Button variant={'primary'} onClick={this.handleAddNewRoute}>
                            Add route
                          </Button>
                        </WithPermissionControlTooltip>
                      </VerticalGroup>
                    </div>
                  ),
                },
                this.renderRoutesFn(),
              ]}
            />

            <IntegrationSendDemoPayloadModal
              alertReceiveChannel={alertReceiveChannel}
              isOpen={isDemoModalOpen}
              onHideOrCancel={() => this.setState({ isDemoModalOpen: false })}
            />
            {isEditTemplateModalOpen && (
              <IntegrationTemplate
                id={id}
                onHide={() => {
                  this.setState({
                    isEditTemplateModalOpen: undefined,
                    isNewRoute: false,
                  });
                  LocationHelper.update({ template: undefined, routeId: undefined }, 'partial');
                }}
                channelFilterId={channelFilterIdForEdit}
                onUpdateTemplates={this.onUpdateTemplatesCallback}
                onUpdateRoute={isNewRoute ? this.onCreateRoutesCallback : this.onUpdateRoutesCallback}
                template={selectedTemplate}
                templateBody={
                  selectedTemplate?.name === 'route_template'
                    ? this.getRoutingTemplate(isNewRoute, channelFilterIdForEdit)
                    : templates[selectedTemplate?.name]
                }
              />
            )}
            {isEditRegexpRouteTemplateModalOpen && (
              <EditRegexpRouteTemplateModal
                alertReceiveChannelId={id}
                channelFilterId={channelFilterIdForEdit}
                template={selectedTemplate}
                onHide={() => this.setState({ isEditRegexpRouteTemplateModalOpen: false })}
                onUpdateRoute={this.onUpdateRoutesCallback}
                onOpenEditIntegrationTemplate={this.openEditTemplateModal}
              />
            )}
          </div>
        )}
      </PageErrorHandlingWrapper>
    );
  }

  getRoutingTemplate = (isRouteNew: boolean, channelFilterId: ChannelFilter['id']) => {
    const {
      store: { alertReceiveChannelStore },
    } = this.props;
    if (isRouteNew) {
      return '{{ (payload.severity == "foo" and "bar" in payload.region) or True }}';
    } else {
      return alertReceiveChannelStore.channelFilters[channelFilterId]?.filtering_term;
    }
  };
  handleAddNewRoute = () => {
    this.setState({ isNewRoute: true });
    this.openEditTemplateModal('route_template');
  };

  renderRoutesFn = (): IntegrationCollapsibleItem[] => {
    const {
      store: { alertReceiveChannelStore },
      match: {
        params: { id },
      },
    } = this.props;

    const templates = alertReceiveChannelStore.templates[id];
    const channelFilterIds = alertReceiveChannelStore.channelFilterIds[id];

    return channelFilterIds.map((channelFilterId: ChannelFilter['id'], routeIndex: number) => ({
      isCollapsible: true,
      isExpanded: false,
      collapsedView: (
        <CollapsedIntegrationRouteDisplay
          alertReceiveChannelId={id}
          channelFilterId={channelFilterId}
          routeIndex={routeIndex}
        />
      ),
      expandedView: (
        <ExpandedIntegrationRouteDisplay
          alertReceiveChannelId={id}
          channelFilterId={channelFilterId}
          routeIndex={routeIndex}
          templates={templates}
          openEditTemplateModal={this.openEditTemplateModal}
          onEditRegexpTemplate={this.handleEditRegexpRouteTemplate}
        />
      ),
    }));
  };

  renderHearbeat = (alertReceiveChannel: AlertReceiveChannel) => {
    const { heartbeatStore, alertReceiveChannelStore } = this.props.store;

    const heartbeatId = alertReceiveChannelStore.alertReceiveChannelToHeartbeat[alertReceiveChannel.id];
    const heartbeat = heartbeatStore.items[heartbeatId];

    const heartbeatStatus = Boolean(heartbeat?.status);

    return (
      <TooltipBadge
        text={undefined}
        className={cx('heartbeat-badge')}
        borderType={alertReceiveChannel.heartbeat?.last_heartbeat_time_verbal ? 'success' : 'danger'}
        customIcon={heartbeatStatus ? <HeartGreenIcon /> : <HeartRedIcon />}
        tooltipTitle={`Last heartbeat: ${alertReceiveChannel.heartbeat?.last_heartbeat_time_verbal || 'never'}`}
        tooltipContent={undefined}
      />
    );
  };

  getAlertReceiveChannelCounterTooltip = () => {
    const { id } = this.props.match.params;
    const { alertReceiveChannelStore } = this.props.store;
    const alertReceiveChannelCounter = alertReceiveChannelStore.counters[id];

    return (
      alertReceiveChannelCounter?.alerts_count +
      ' alert' +
      (alertReceiveChannelCounter?.alerts_count === 1 ? '' : 's') +
      ' in ' +
      alertReceiveChannelCounter?.alert_groups_count +
      ' alert group' +
      (alertReceiveChannelCounter?.alert_groups_count === 1 ? '' : 's')
    );
  };

  handleSlackChannelChange = () => {};

  handleEditRegexpRouteTemplate = (channelFilterId) => {
    this.setState({ isEditRegexpRouteTemplateModalOpen: true, channelFilterIdForEdit: channelFilterId });
  };

  onCreateRoutesCallback = ({ route_template }: { route_template: string }) => {
    const { alertReceiveChannelStore, escalationPolicyStore } = this.props.store;
    const {
      params: { id },
    } = this.props.match;

    alertReceiveChannelStore
      .createChannelFilter({
        order: 0,
        alert_receive_channel: id,
        filtering_term: route_template,

        // TODO: need to figure out this value
        filtering_term_type: 1,
      })
      .then((channelFilter: ChannelFilter) => {
        alertReceiveChannelStore.updateChannelFilters(id, true).then(() => {
          // @ts-ignore
          escalationPolicyStore.updateEscalationPolicies(channelFilter.escalation_chain);
        });
      })
      .catch((err) => {
        const errors = get(err, 'response.data');
        if (errors?.non_field_errors) {
          openErrorNotification(errors.non_field_errors);
        }
      });
  };

  onUpdateRoutesCallback = (
    { route_template }: { route_template: string },
    channelFilterId,
    filteringTermType?: number
  ) => {
    const { alertReceiveChannelStore, escalationPolicyStore } = this.props.store;
    const {
      params: { id },
    } = this.props.match;

    alertReceiveChannelStore
      .saveChannelFilter(channelFilterId, {
        filtering_term: route_template,

        // TODO: need to figure out this value
        filtering_term_type: filteringTermType,
      })
      .then((channelFilter: ChannelFilter) => {
        alertReceiveChannelStore.updateChannelFilters(id, true).then(() => {
          // @ts-ignore
          escalationPolicyStore.updateEscalationPolicies(channelFilter.escalation_chain);
        });
      })
      .catch((err) => {
        const errors = get(err, 'response.data');
        if (errors?.non_field_errors) {
          openErrorNotification(errors.non_field_errors);
        }
      });
  };

  onUpdateTemplatesCallback = (data) => {
    const {
      store,
      match: {
        params: { id },
      },
    } = this.props;

    store.alertReceiveChannelStore
      .saveTemplates(id, data)
      .then(() => {
        openNotification('The Alert templates have been updated');
      })
      .catch((err) => {
        if (err.response?.data?.length > 0) {
          openErrorNotification(err.response.data);
        } else {
          openErrorNotification(err.message);
        }
      });
  };

  getTemplatesList = (): CascaderOption[] => INTEGRATION_TEMPLATES_LIST;

  openEditTemplateModal = (templateName, channelFilterId?: ChannelFilter['id']) => {
    this.setState({ selectedTemplate: templateForEdit[templateName] });
    this.setState({ isEditTemplateModalOpen: true });

    if (channelFilterId) {
      this.setState({ channelFilterIdForEdit: channelFilterId });
    }
  };

  onRemovalFn = (id: AlertReceiveChannel['id']) => {
    const {
      store: { alertReceiveChannelStore },
      history,
    } = this.props;

    alertReceiveChannelStore.deleteAlertReceiveChannel(id).then(() => history.push(`${PLUGIN_ROOT}/integrations_2/`));
  };

  deleteIntegration = (_id: AlertReceiveChannel['id'], _closeMenu: () => void) => {};

  openIntegrationSettings = (_id: AlertReceiveChannel['id'], _closeMenu: () => void) => {};

  openStartMaintenance = (_id: AlertReceiveChannel['id'], _closeMenu: () => void) => {};

  openHearbeat = (_id: AlertReceiveChannel['id'], _closeMenu: () => void) => {};

  async loadIntegration() {
    const {
      store: { alertReceiveChannelStore },
      match: {
        params: { id },
      },
    } = this.props;

    const promises = [];

    if (!alertReceiveChannelStore.items[id]) {
      // See what happens if the request fails
      promises.push(alertReceiveChannelStore.loadItem(id));
    }

    if (!alertReceiveChannelStore.counters?.length) {
      promises.push(alertReceiveChannelStore.updateCounters());
    }

    if (!alertReceiveChannelStore.channelFilterIds[id]) {
      promises.push(await alertReceiveChannelStore.updateChannelFilters(id));
    }

    await Promise.all(promises);
  }
}

const DemoNotification: React.FC = () => {
  return (
    <div>
      Demo alert was generated. Find it on the
      <PluginLink query={{ page: 'alert-groups' }}> "Alert Groups" </PluginLink>
      page and make sure it didn't freak out your colleagues 😉
    </div>
  );
};

const HamburgerMenu: React.FC<{ openMenu: React.MouseEventHandler<HTMLElement> }> = ({ openMenu }) => {
  const ref = useRef<HTMLDivElement>();

  return (
    <div
      ref={ref}
      className={cx('hamburger-menu')}
      onClick={() => {
        const boundingRect = ref.current.getBoundingClientRect();

        openMenu({
          pageX: boundingRect.right - ACTIONS_LIST_WIDTH + ACTIONS_LIST_BORDER * 2,
          pageY: boundingRect.top + boundingRect.height,
        } as any);
      }}
    >
      <Icon size="sm" name="ellipsis-v" />
    </div>
  );
};

interface IntegrationSendDemoPayloadModalProps {
  isOpen: boolean;
  alertReceiveChannel: AlertReceiveChannel;
  onHideOrCancel: () => void;
}

const IntegrationSendDemoPayloadModal: React.FC<IntegrationSendDemoPayloadModalProps> = ({
  alertReceiveChannel,
  isOpen,
  onHideOrCancel,
}) => {
  const { alertReceiveChannelStore } = useStore();

  return (
    <Modal
      closeOnEscape
      isOpen={isOpen}
      onDismiss={onHideOrCancel}
      title={`Send demo alert to ${alertReceiveChannel.verbal_name}`}
    >
      <VerticalGroup>
        <HorizontalGroup spacing={'xs'}>
          <Text type={'secondary'}>Alert Payload</Text>
          <Tooltip content={'TODO'} placement={'top-start'}>
            <Icon name={'info-circle'} />
          </Tooltip>
        </HorizontalGroup>

        <SourceCode showCopyToClipboard={false}>{getDemoAlertJSON()}</SourceCode>

        <HorizontalGroup justify={'flex-end'} spacing={'md'}>
          <Button variant={'secondary'} onClick={onHideOrCancel}>
            Cancel
          </Button>
          <CopyToClipboard text={getCurlText()} onCopy={() => openNotification('CURL copied!')}>
            <Button variant={'secondary'}>Copy as CURL</Button>
          </CopyToClipboard>
          <Button variant={'primary'} onClick={sendDemoAlert}>
            Send Alert
          </Button>
        </HorizontalGroup>
      </VerticalGroup>
    </Modal>
  );

  function sendDemoAlert() {
    alertReceiveChannelStore.sendDemoAlert(alertReceiveChannel.id).then(() => {
      alertReceiveChannelStore.updateCounters();
      openNotification(<DemoNotification />);
      onHideOrCancel();
    });
  }

  function getCurlText() {
    // TODO add this
    return `curl -X POST [URL]
    -H "Content-Type: application/json" 
    -d "[JSON data]"`;
  }

  function getDemoAlertJSON() {
    return JSON.stringify(INTEGRATION_DEMO_PAYLOAD, null, 4);
  }
};

const HowToConnectComponent: React.FC<{ id: AlertReceiveChannel['id'] }> = ({ id }) => {
  const { alertReceiveChannelStore } = useStore();
  const alertReceiveChannelCounter = alertReceiveChannelStore.counters[id];
  const alertReceiveChannel = alertReceiveChannelStore.items[id];
  const isAlertManager = alertReceiveChannel.integration === DATASOURCE_ALERTING;
  const hasAlerts = !!alertReceiveChannelCounter?.alerts_count;

  return (
    <IntegrationBlock
      hasCollapsedBorder={false}
      heading={
        <div className={cx('how-to-connect__container')}>
          <Tag color={getVar('--tag-secondary')} className={cx('how-to-connect__tag')}>
            <Text type="primary" size="small">
              HTTP Endpoint
            </Text>
          </Tag>
          <IntegrationMaskedInputField value={alertReceiveChannelStore.items[id].integration_url} />
          <a href="https://grafana.com/docs/oncall/latest/integrations/" target="_blank" rel="noreferrer">
            <Text type="link" size="small" onClick={openHowToConnect}>
              <HorizontalGroup>
                How to connect
                <Icon name="external-link-alt" />
              </HorizontalGroup>
            </Text>
          </a>
        </div>
      }
      content={isAlertManager || !hasAlerts ? renderContent() : null}
    />
  );

  function openHowToConnect() {}

  function renderContent() {
    return (
      <div className={cx('integration__alertsPanel')}>
        <VerticalGroup justify={'flex-start'} spacing={'xs'}>
          {!hasAlerts && (
            <HorizontalGroup spacing={'xs'}>
              <LoadingPlaceholder text="" className={cx('loadingPlaceholder')} />
              <Text type={'primary'}>No alerts yet; try to send a demo alert</Text>
            </HorizontalGroup>
          )}

          {isAlertManager && (
            <HorizontalGroup spacing={'xs'}>
              <Icon name="list-ui-alt" size="md" />
              <a href="/alerting/notifications" target="_blank">
                <Text type={'link'}>Contact Point</Text>
              </a>
              <Text type={'secondary'}>and</Text>
              <a href="/alerting/routes" target="_blank">
                <Text type={'link'}>Notification Policy</Text>
              </a>
              <Text type={'secondary'}>created in Grafana Alerting</Text>
            </HorizontalGroup>
          )}
        </VerticalGroup>
      </div>
    );
  }
};

export default withRouter(withMobXProviderContext(Integration2));
