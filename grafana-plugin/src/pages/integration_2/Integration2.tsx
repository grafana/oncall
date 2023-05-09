import React, { useRef, useState } from 'react';

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
  ConfirmModal,
} from '@grafana/ui';
import cn from 'classnames/bind';
import { get } from 'lodash-es';
import { observer } from 'mobx-react';
import CopyToClipboard from 'react-copy-to-clipboard';
import Emoji from 'react-emoji-render';
import { RouteComponentProps, useHistory, withRouter } from 'react-router-dom';

import { TemplateForEdit, templateForEdit } from 'components/AlertTemplates/AlertTemplatesForm.config';
import IntegrationCollapsibleTreeView, {
  IntegrationCollapsibleItem,
} from 'components/IntegrationCollapsibleTreeView/IntegrationCollapsibleTreeView';
import IntegrationInputField from 'components/IntegrationInputField/IntegrationInputField';
import IntegrationLogo from 'components/IntegrationLogo/IntegrationLogo';
import PageErrorHandlingWrapper, { PageBaseState } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper';
import { initErrorDataState } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper.helpers';
import PluginLink from 'components/PluginLink/PluginLink';
import SourceCode from 'components/SourceCode/SourceCode';
import Tag from 'components/Tag/Tag';
import Text from 'components/Text/Text';
import TooltipBadge from 'components/TooltipBadge/TooltipBadge';
import { WithContextMenu } from 'components/WithContextMenu/WithContextMenu';
import EditRegexpRouteTemplateModal from 'containers/EditRegexpRouteTemplateModal/EditRegexpRouteTemplateModal';
import IntegrationTemplate from 'containers/IntegrationTemplate/IntegrationTemplate';
import MaintenanceForm from 'containers/MaintenanceForm/MaintenanceForm';
import TeamName from 'containers/TeamName/TeamName';
import UserDisplayWithAvatar from 'containers/UserDisplay/UserDisplayWithAvatar';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { HeartGreenIcon, HeartRedIcon } from 'icons';
import { AlertReceiveChannel } from 'models/alert_receive_channel';
import { ChannelFilter } from 'models/channel_filter';
import { MaintenanceType } from 'models/maintenance/maintenance.types';
import { PageProps, WithStoreProps } from 'state/types';
import { useStore } from 'state/useStore';
import { withMobXProviderContext } from 'state/withStore';
import { openNotification, openErrorNotification } from 'utils';
import { getVar } from 'utils/DOM';
import { UserActions } from 'utils/authorization';
import { DATASOURCE_ALERTING, PLUGIN_ROOT } from 'utils/consts';

import CollapsedIntegrationRouteDisplay from './CollapsedIntegrationRouteDisplay';
import ExpandedIntegrationRouteDisplay from './ExpandedIntegrationRouteDisplay';
import { INTEGRATION_DEMO_PAYLOAD, INTEGRATION_TEMPLATES_LIST } from './Integration2.config';
import IntegrationHelper from './Integration2.helper';
import styles from './Integration2.module.scss';
import Integration2HeartbeatForm from './Integration2HeartbeatForm';
import IntegrationBlock from './IntegrationBlock';
import IntegrationTemplateList from './IntegrationTemplatesList';
import IntegrationForm2 from 'containers/IntegrationForm/IntegrationForm2';

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
    } = this.props;
    const {
      store: { alertReceiveChannelStore },
    } = this.props;

    await Promise.all([this.loadIntegration(), alertReceiveChannelStore.updateTemplates(id)]);
  }

  render() {
    const {
      errorData,
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

              <IntegrationActions alertReceiveChannel={alertReceiveChannel} />
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
                  <HorizontalGroup spacing="xs">
                    <IntegrationLogo scale={0.08} integration={integration} />
                    <Text type="primary">{integration?.display_name}</Text>
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
                          <Tag
                            color={getVar('--tag-secondary-transparent')}
                            border={getVar('--border-weak')}
                            className={cx('tag')}
                          >
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
                          <Tag
                            color={getVar('--tag-secondary-transparent')}
                            border={getVar('--border-weak')}
                            className={cx('tag')}
                          >
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

            {isEditTemplateModalOpen && (
              <IntegrationTemplate
                id={id}
                onHide={() => {
                  this.setState({
                    isEditTemplateModalOpen: undefined,
                    isNewRoute: false,
                  });
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

  handleEditRegexpRouteTemplate = (_templateRegexpBody, _templateJijja2Body, channelFilterId) => {
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

interface IntegrationActionsProps {
  alertReceiveChannel: AlertReceiveChannel;
}

const IntegrationActions: React.FC<IntegrationActionsProps> = ({ alertReceiveChannel }) => {
  const { maintenanceStore, alertReceiveChannelStore } = useStore();

  const history = useHistory();

  const [confirmModal, setConfirmModal] = useState<{
    isOpen: boolean;
    title: any;
    dismissText: string;
    confirmText: string;
    body?: React.ReactNode;
    description?: string;
    confirmationText?: string;
    onConfirm: () => void;
  }>(undefined);

  const [isIntegrationSettingsOpen, setIsIntegrationSettingsOpen] = useState(false);
  const [isHearbeatFormOpen, setIsHearbeatFormOpen] = useState(false);
  const [isDemoModalOpen, setIsDemoModalOpen] = useState(false);
  const [maintenanceData, setMaintenanceData] = useState<{
    disabled: boolean;
    alert_receive_channel_id: AlertReceiveChannel['id'];
  }>(undefined);

  const { id } = alertReceiveChannel;

  return (
    <>
      {confirmModal && (
        <ConfirmModal
          isOpen={confirmModal.isOpen}
          title={confirmModal.title}
          confirmText={confirmModal.confirmText}
          dismissText="Cancel"
          body={confirmModal.body}
          description={confirmModal.description}
          confirmationText={confirmModal.confirmationText}
          onConfirm={confirmModal.onConfirm}
          onDismiss={() => setConfirmModal(undefined)}
        />
      )}

      <IntegrationSendDemoPayloadModal
        alertReceiveChannel={alertReceiveChannel}
        isOpen={isDemoModalOpen}
        onHideOrCancel={() => setIsDemoModalOpen(false)}
      />

      {isIntegrationSettingsOpen && (
        <IntegrationForm2
          isTableView={false}
          onHide={() => setIsIntegrationSettingsOpen(false)}
          onUpdate={() => alertReceiveChannelStore.updateItem(alertReceiveChannel['id'])}
          id={alertReceiveChannel['id']}
        />
      )}

      {isHearbeatFormOpen && (
        <Integration2HeartbeatForm
          alertReceveChannelId={alertReceiveChannel['id']}
          onClose={() => setIsHearbeatFormOpen(false)}
        />
      )}

      {maintenanceData && (
        <MaintenanceForm
          initialData={maintenanceData}
          onUpdate={() => alertReceiveChannelStore.updateItem(alertReceiveChannel.id)}
          onHide={() => setMaintenanceData(undefined)}
        />
      )}

      <div className={cx('integration__actions')}>
        <WithPermissionControlTooltip userAction={UserActions.IntegrationsTest}>
          <Button variant="secondary" size="md" onClick={() => setIsDemoModalOpen(true)} data-testid="send-demo-alert">
            Send demo alert
          </Button>
        </WithPermissionControlTooltip>

        <WithContextMenu
          renderMenuItems={() => (
            <div className={cx('integration__actionsList')} id="integration-menu-options">
              <div className={cx('integration__actionItem')} onClick={() => openIntegrationSettings()}>
                <Text type="primary">Integration Settings</Text>
              </div>

              <div className={cx('integration__actionItem')} onClick={() => setIsHearbeatFormOpen(true)}>
                Hearbeat
              </div>

              {!alertReceiveChannel.maintenance_till && (
                <WithPermissionControlTooltip userAction={UserActions.MaintenanceWrite}>
                  <div className={cx('integration__actionItem')} onClick={openStartMaintenance}>
                    <Text type="primary">Start Maintenance</Text>
                  </div>
                </WithPermissionControlTooltip>
              )}

              {alertReceiveChannel.maintenance_till && (
                <WithPermissionControlTooltip userAction={UserActions.MaintenanceWrite}>
                  <div className={cx('integration__actionItem')}>
                    <div
                      onClick={() => {
                        setConfirmModal({
                          isOpen: true,
                          confirmText: 'Stop',
                          dismissText: 'Cancel',
                          onConfirm: onStopMaintenance,
                          title: (
                            <>
                              Are you sure you want to stop the maintenance for{' '}
                              <Emoji text={alertReceiveChannel.verbal_name} />?
                            </>
                          ),
                        });
                      }}
                    >
                      <Text type="primary">Stop Maintenance</Text>
                    </div>
                  </div>
                </WithPermissionControlTooltip>
              )}

              <div className="thin-line-break" />

              <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
                <div className={cx('integration__actionItem')}>
                  <div
                    onClick={() => {
                      setConfirmModal({
                        isOpen: true,
                        title: 'Are you sure you want to delete integration?',
                        body: <>This action cannot be undone.</>,
                        onConfirm: deleteIntegration,
                        dismissText: 'Cancel',
                        confirmText: 'Delete',
                      });
                    }}
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
          {({ openMenu }) => <HamburgerMenu openMenu={openMenu} />}
        </WithContextMenu>
      </div>
    </>
  );

  function deleteIntegration() {
    alertReceiveChannelStore
      .deleteAlertReceiveChannel(alertReceiveChannel.id)
      .then(() => history.push(`${PLUGIN_ROOT}/integrations_2`));
  }

  function openIntegrationSettings() {
    setIsIntegrationSettingsOpen(true);
  }

  function openStartMaintenance() {
    setMaintenanceData({ disabled: true, alert_receive_channel_id: alertReceiveChannel.id });
  }

  function onStopMaintenance() {
    setConfirmModal(undefined);

    maintenanceStore
      .stopMaintenanceMode(MaintenanceType.alert_receive_channel, id)
      .then(() => maintenanceStore.updateMaintenances())
      .then(() => alertReceiveChannelStore.updateItem(alertReceiveChannel.id));
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
          <Tag
            color={getVar('--tag-secondary-transparent')}
            border={getVar('--border-weak')}
            className={cx('how-to-connect__tag')}
          >
            <Text type="primary" size="small">
              HTTP Endpoint
            </Text>
          </Tag>
          <IntegrationInputField
            value={alertReceiveChannelStore.items[id].integration_url}
            className={cx('integration__input-field')}
          />
          <a href="https://grafana.com/docs/oncall/latest/integrations/" target="_blank" rel="noreferrer">
            <Text type="link" size="small">
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
