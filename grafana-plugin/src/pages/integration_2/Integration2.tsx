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
  Drawer,
} from '@grafana/ui';
import cn from 'classnames/bind';
import { get } from 'lodash-es';
import { observer } from 'mobx-react';
import CopyToClipboard from 'react-copy-to-clipboard';
import Emoji from 'react-emoji-render';
import { RouteComponentProps, useHistory, withRouter } from 'react-router-dom';
import { debounce } from 'throttle-debounce';

import { TemplateForEdit, templateForEdit } from 'components/AlertTemplates/AlertTemplatesForm.config';
import IntegrationCollapsibleTreeView, {
  IntegrationCollapsibleItem,
} from 'components/IntegrationCollapsibleTreeView/IntegrationCollapsibleTreeView';
import IntegrationInputField from 'components/IntegrationInputField/IntegrationInputField';
import IntegrationLogo from 'components/IntegrationLogo/IntegrationLogo';
import MonacoEditor, { MONACO_LANGUAGE } from 'components/MonacoEditor/MonacoEditor';
import PageErrorHandlingWrapper, { PageBaseState } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper';
import { initErrorDataState } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper.helpers';
import PluginLink from 'components/PluginLink/PluginLink';
import Tag from 'components/Tag/Tag';
import Text from 'components/Text/Text';
import TooltipBadge from 'components/TooltipBadge/TooltipBadge';
import { WithContextMenu } from 'components/WithContextMenu/WithContextMenu';
import EditRegexpRouteTemplateModal from 'containers/EditRegexpRouteTemplateModal/EditRegexpRouteTemplateModal';
import IntegrationForm2 from 'containers/IntegrationForm/IntegrationForm2';
import IntegrationTemplate from 'containers/IntegrationTemplate/IntegrationTemplate';
import MaintenanceForm from 'containers/MaintenanceForm/MaintenanceForm';
import TeamName from 'containers/TeamName/TeamName';
import UserDisplayWithAvatar from 'containers/UserDisplay/UserDisplayWithAvatar';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { HeartIcon, HeartRedIcon } from 'icons';
import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { ChannelFilter } from 'models/channel_filter';
import { MaintenanceType } from 'models/maintenance/maintenance.types';
import { API_HOST, API_PATH_PREFIX } from 'network';
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
import { INTEGRATION_TEMPLATES_LIST, MONACO_PAYLOAD_OPTIONS } from './Integration2.config';
import IntegrationHelper from './Integration2.helper';
import styles from './Integration2.module.scss';
import Integration2HeartbeatForm from './Integration2HeartbeatForm';
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
  isTemplateSettingsOpen: boolean;
  newRoutes: string[];
  isAddingRoute: boolean;
}

const ACTIONS_LIST_WIDTH = 160;
const ACTIONS_LIST_BORDER = 2;
const NEW_ROUTE_DEFAULT = '{{ (payload.severity == "foo" and "bar" in payload.region) or True }}';

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
      isTemplateSettingsOpen: false,
      newRoutes: [],
      isAddingRoute: false,
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
      isEditTemplateModalOpen,
      selectedTemplate,
      isEditRegexpRouteTemplateModalOpen,
      channelFilterIdForEdit,
      isTemplateSettingsOpen,
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
            {isTemplateSettingsOpen && (
              <Drawer
                width="75%"
                scrollableContent
                title="Template Settings"
                onClose={() => this.setState({ isTemplateSettingsOpen: false })}
                closeOnMaskClick={false}
              >
                <IntegrationBlock
                  className={cx('template-drawer')}
                  hasCollapsedBorder
                  heading={undefined}
                  content={
                    <IntegrationTemplateList
                      alertReceiveChannelId={alertReceiveChannel.id}
                      openEditTemplateModal={this.openEditTemplateModal}
                      templates={templates}
                    />
                  }
                />
              </Drawer>
            )}

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
                  <PluginLink
                    className={cx('hover-button')}
                    target="_blank"
                    query={{ page: 'alert-groups', integration: alertReceiveChannel.id }}
                  >
                    <TooltipBadge
                      borderType="primary"
                      tooltipTitle={undefined}
                      tooltipContent={this.getAlertReceiveChannelCounterTooltip()}
                      text={
                        alertReceiveChannelCounter?.alerts_count + '/' + alertReceiveChannelCounter?.alert_groups_count
                      }
                    />
                  </PluginLink>
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
                  customIcon: 'layer-group',
                  isExpanded: false,
                  isCollapsible: false,
                  canHoverIcon: false,
                  expandedView: (
                    <IntegrationBlock
                      hasCollapsedBorder
                      heading={
                        <div className={cx('templates__container')}>
                          <Tag
                            color={getVar('--tag-secondary-transparent')}
                            border={getVar('--border-weak')}
                            className={cx('tag')}
                          >
                            <Text type="primary" size="small">
                              Templates
                            </Text>
                          </Tag>

                          <div className={cx('templates__content')}>
                            <HorizontalGroup>
                              <HorizontalGroup spacing={'xs'}>
                                <Text type="secondary">Grouping:</Text>
                                <Text type="primary">
                                  {IntegrationHelper.truncateLine(templates['grouping_id_template'] || '')}
                                </Text>
                              </HorizontalGroup>

                              <HorizontalGroup spacing={'xs'}>
                                <Text type="secondary">Autoresolve:</Text>
                                <Text type="primary">
                                  {IntegrationHelper.truncateLine(templates['resolve_condition_template'] || '')}
                                </Text>
                              </HorizontalGroup>

                              <HorizontalGroup spacing={'xs'}>
                                <Text type="secondary">Visualisation:</Text>
                                <Text type="primary">Multiple</Text>
                              </HorizontalGroup>
                            </HorizontalGroup>

                            <div className={cx('templates__edit')}>
                              <Button
                                variant={'secondary'}
                                icon="edit"
                                size={'sm'}
                                tooltip="Edit"
                                onClick={() => this.setState({ isTemplateSettingsOpen: true })}
                              />
                            </div>
                          </div>
                        </div>
                      }
                      content={null}
                    />
                  ),
                  collapsedView: undefined,
                },
                {
                  customIcon: 'code-branch',
                  isCollapsible: false,
                  collapsedView: null,
                  canHoverIcon: false,
                  expandedView: (
                    <div className={cx('routesSection')}>
                      <VerticalGroup spacing="md">
                        <Text type={'primary'} className={cx('routesSection__heading')}>
                          Routes
                        </Text>
                        <HorizontalGroup>
                          <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
                            <Button
                              variant={'primary'}
                              className={cx('routesSection__add')}
                              onClick={this.handleAddNewRoute}
                            >
                              Add route
                            </Button>
                          </WithPermissionControlTooltip>
                          {this.state.isAddingRoute && <LoadingPlaceholder text="Loading..." />}
                        </HorizontalGroup>
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
                  });
                  LocationHelper.update({ template: undefined, routeId: undefined }, 'partial');
                }}
                channelFilterId={channelFilterIdForEdit}
                onUpdateTemplates={this.onUpdateTemplatesCallback}
                onUpdateRoute={this.onUpdateRoutesCallback}
                template={selectedTemplate}
                templateBody={
                  selectedTemplate?.name === 'route_template'
                    ? this.getRoutingTemplate(channelFilterIdForEdit)
                    : templates[selectedTemplate?.name]
                }
                templates={templates}
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

  getRoutingTemplate = (channelFilterId: ChannelFilter['id']) => {
    const {
      store: { alertReceiveChannelStore },
    } = this.props;

    return alertReceiveChannelStore.channelFilters[channelFilterId]?.filtering_term;
  };

  handleAddNewRoute = () => {
    const { alertReceiveChannelStore, escalationPolicyStore } = this.props.store;
    const {
      params: { id },
    } = this.props.match;

    this.setState(
      {
        isAddingRoute: true,
      },
      () => {
        alertReceiveChannelStore
          .createChannelFilter({
            order: 0,
            alert_receive_channel: id,
            filtering_term: NEW_ROUTE_DEFAULT,
            filtering_term_type: 1, // non-regex
          })
          .then(async (channelFilter: ChannelFilter) => {
            this.setState({ isAddingRoute: false, newRoutes: this.state.newRoutes.concat(channelFilter.id) });
            await alertReceiveChannelStore.updateChannelFilters(id, true);
            await escalationPolicyStore.updateEscalationPolicies(channelFilter.escalation_chain);
            openNotification('A new route has been added');
          })
          .catch((err) => {
            const errors = get(err, 'response.data');
            if (errors?.non_field_errors) {
              openErrorNotification(errors.non_field_errors);
            }
          });
      }
    );
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

    return channelFilterIds.map(
      (channelFilterId: ChannelFilter['id'], routeIndex: number) =>
        ({
          isCollapsible: true,
          // this will keep new routes expanded at the very first time
          isExpanded: this.state.newRoutes.indexOf(channelFilterId) > -1 ? true : false,
          onStateChange: () => {
            if (this.state.newRoutes.indexOf(channelFilterId) > -1) {
              // this will close them on user action
              this.setState((prevState) => ({ newRoutes: prevState.newRoutes.filter((r) => r !== channelFilterId) }));
            }
          },
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
        } as IntegrationCollapsibleItem)
    );
  };

  renderHearbeat = (alertReceiveChannel: AlertReceiveChannel) => {
    const { heartbeatStore, alertReceiveChannelStore } = this.props.store;

    const heartbeatId = alertReceiveChannelStore.alertReceiveChannelToHeartbeat[alertReceiveChannel.id];
    const heartbeat = heartbeatStore.items[heartbeatId];

    const heartbeatStatus = Boolean(heartbeat?.status);

    if (
      !alertReceiveChannel.is_available_for_integration_heartbeat ||
      alertReceiveChannel.heartbeat?.last_heartbeat_time_verbal === null
    ) {
      return null;
    }

    return (
      <TooltipBadge
        text={undefined}
        className={cx('heartbeat-badge')}
        borderType={heartbeatStatus ? 'success' : 'danger'}
        customIcon={heartbeatStatus ? <HeartIcon /> : <HeartRedIcon />}
        tooltipTitle={`Last heartbeat: ${alertReceiveChannel.heartbeat?.last_heartbeat_time_verbal}`}
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

  onUpdateRoutesCallback = (
    { route_template }: { route_template: string },
    channelFilterId: ChannelFilter['id'],
    filteringTermType?: number
  ) => {
    const { alertReceiveChannelStore, escalationPolicyStore } = this.props.store;
    const {
      params: { id },
    } = this.props.match;

    alertReceiveChannelStore
      .saveChannelFilter(channelFilterId, {
        filtering_term: route_template,
        filtering_term_type: filteringTermType,
      })
      .then((channelFilter: ChannelFilter) => {
        alertReceiveChannelStore.updateChannelFilters(id, true).then(() => {
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
    this.setState({
      isEditTemplateModalOpen: true,
      selectedTemplate: templateForEdit[templateName],
    });

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
  const [demoPayload, setDemoPayload] = useState<string>(
    JSON.stringify(alertReceiveChannel.demo_alert_payload, null, '\t')
  );
  let onPayloadChangeDebounced = debounce(100, onPayloadChange);

  return (
    <Modal
      closeOnBackdropClick={false}
      closeOnEscape
      isOpen={isOpen}
      onDismiss={onHideOrCancel}
      title={`Send demo alert to ${alertReceiveChannel.verbal_name}`}
    >
      <VerticalGroup>
        <HorizontalGroup spacing={'xs'}>
          <Text type={'secondary'}>Alert Payload</Text>
          <Tooltip
            content={
              <>
                A demo alert will be generated. You can find it on the <strong>Alert Groups</strong> page
              </>
            }
            placement={'top-start'}
          >
            <Icon name={'info-circle'} />
          </Tooltip>
        </HorizontalGroup>

        <div className={cx('integration__payloadInput')}>
          <MonacoEditor
            value={JSON.stringify(alertReceiveChannel.demo_alert_payload, null, '\t')}
            disabled={true}
            height={`200px`}
            useAutoCompleteList={false}
            language={MONACO_LANGUAGE.json}
            data={undefined}
            monacoOptions={MONACO_PAYLOAD_OPTIONS}
            showLineNumbers={false}
            onChange={onPayloadChangeDebounced}
          />
        </div>

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

  function onPayloadChange(value: string) {
    setDemoPayload(value);
  }

  function sendDemoAlert() {
    let parsedPayload = undefined;
    try {
      parsedPayload = JSON.parse(demoPayload);
    } catch (ex) {}

    alertReceiveChannelStore.sendDemoAlert(alertReceiveChannel.id, parsedPayload).then(() => {
      alertReceiveChannelStore.updateCounters();
      openNotification(<DemoNotification />);
      onHideOrCancel();
    });
  }

  function getCurlText() {
    return (
      `curl '${API_HOST}${API_PATH_PREFIX}${API_PATH_PREFIX}/alert_receive_channels/${alertReceiveChannel.id}/send_demo_alert/'` +
      ` -XPOST -H 'Content-Type: application/json'` +
      `--data-raw '{"demo_alert_payload":{"alerts":[{"a":"b"}]}}' --compressed`
    );
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

      {alertReceiveChannel.demo_alert_enabled && (
        <IntegrationSendDemoPayloadModal
          alertReceiveChannel={alertReceiveChannel}
          isOpen={isDemoModalOpen}
          onHideOrCancel={() => setIsDemoModalOpen(false)}
        />
      )}

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
          <Button
            variant="secondary"
            size="md"
            onClick={() => setIsDemoModalOpen(true)}
            data-testid="send-demo-alert"
            disabled={!alertReceiveChannel.demo_alert_enabled}
            tooltip={alertReceiveChannel.demo_alert_enabled ? '' : 'Demo Alerts are not enabled for this integration'}
          >
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
                        title: (
                          <>
                            Are you sure you want to delete <Emoji text={alertReceiveChannel.verbal_name} />{' '}
                            integration?
                          </>
                        ),
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
              <Icon name="fa fa-spinner" size="md" className={cx('loadingPlaceholder')} />
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
