import React, { useState } from 'react';

import {
  Button,
  HorizontalGroup,
  VerticalGroup,
  Icon,
  LoadingPlaceholder,
  CascaderOption,
  IconButton,
  ConfirmModal,
  Drawer,
  Alert,
} from '@grafana/ui';
import cn from 'classnames/bind';
import { get, noop } from 'lodash-es';
import { observer } from 'mobx-react';
import CopyToClipboard from 'react-copy-to-clipboard';
import Emoji from 'react-emoji-render';
import { RouteComponentProps, useHistory, withRouter } from 'react-router-dom';

import { templateForEdit } from 'components/AlertTemplates/AlertTemplatesForm.config';
import { TemplateForEdit } from 'components/AlertTemplates/CommonAlertTemplatesForm.config';
import HamburgerMenu from 'components/HamburgerMenu/HamburgerMenu';
import IntegrationCollapsibleTreeView, {
  IntegrationCollapsibleItem,
} from 'components/IntegrationCollapsibleTreeView/IntegrationCollapsibleTreeView';
import IntegrationContactPoint from 'components/IntegrationContactPoint/IntegrationContactPoint';
import IntegrationHowToConnect from 'components/IntegrationHowToConnect/IntegrationHowToConnect';
import IntegrationLogo from 'components/IntegrationLogo/IntegrationLogo';
import IntegrationSendDemoAlertModal from 'components/IntegrationSendDemoAlertModal/IntegrationSendDemoAlertModal';
import IntegrationBlock from 'components/Integrations/IntegrationBlock';
import PageErrorHandlingWrapper, { PageBaseState } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper';
import { initErrorDataState } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper.helpers';
import PluginLink from 'components/PluginLink/PluginLink';
import Tag from 'components/Tag/Tag';
import Text from 'components/Text/Text';
import TooltipBadge from 'components/TooltipBadge/TooltipBadge';
import { WithContextMenu } from 'components/WithContextMenu/WithContextMenu';
import EditRegexpRouteTemplateModal from 'containers/EditRegexpRouteTemplateModal/EditRegexpRouteTemplateModal';
import CollapsedIntegrationRouteDisplay from 'containers/IntegrationContainers/CollapsedIntegrationRouteDisplay/CollapsedIntegrationRouteDisplay';
import ExpandedIntegrationRouteDisplay from 'containers/IntegrationContainers/ExpandedIntegrationRouteDisplay/ExpandedIntegrationRouteDisplay';
import IntegrationHeartbeatForm from 'containers/IntegrationContainers/IntegrationHeartbeatForm/IntegrationHeartbeatForm';
import IntegrationTemplateList from 'containers/IntegrationContainers/IntegrationTemplatesList';
import IntegrationForm from 'containers/IntegrationForm/IntegrationForm';
import IntegrationTemplate from 'containers/IntegrationTemplate/IntegrationTemplate';
import MaintenanceForm from 'containers/MaintenanceForm/MaintenanceForm';
import TeamName from 'containers/TeamName/TeamName';
import UserDisplayWithAvatar from 'containers/UserDisplay/UserDisplayWithAvatar';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { HeartIcon, HeartRedIcon } from 'icons';
import {
  AlertReceiveChannel,
  AlertReceiveChannelCounters,
} from 'models/alert_receive_channel/alert_receive_channel.types';
import { AlertTemplatesDTO } from 'models/alert_templates';
import { ChannelFilter } from 'models/channel_filter';
import { INTEGRATION_TEMPLATES_LIST } from 'pages/integration/Integration.config';
import IntegrationHelper from 'pages/integration/Integration.helper';
import styles from 'pages/integration/Integration.module.scss';
import { PageProps, SelectOption, WithStoreProps } from 'state/types';
import { useStore } from 'state/useStore';
import { withMobXProviderContext } from 'state/withStore';
import { openNotification, openErrorNotification } from 'utils';
import { getVar } from 'utils/DOM';
import LocationHelper from 'utils/LocationHelper';
import { UserActions } from 'utils/authorization';
import { PLUGIN_ROOT } from 'utils/consts';
import sanitize from 'utils/sanitize';

const cx = cn.bind(styles);

interface IntegrationProps extends WithStoreProps, PageProps, RouteComponentProps<{ id: string }> {}

interface IntegrationState extends PageBaseState {
  isLoading: boolean;
  isDemoModalOpen: boolean;
  isEditTemplateModalOpen: boolean;
  selectedTemplate: TemplateForEdit;
  isEditRegexpRouteTemplateModalOpen: boolean;
  channelFilterIdForEdit: ChannelFilter['id'];
  isTemplateSettingsOpen: boolean;
  isAddingRoute: boolean;
  openRoutes: string[];
}

const NEW_ROUTE_DEFAULT = '';

@observer
class Integration extends React.Component<IntegrationProps, IntegrationState> {
  constructor(props: IntegrationProps) {
    super(props);

    this.state = {
      isLoading: true,
      errorData: initErrorDataState(),
      isDemoModalOpen: false,
      isEditTemplateModalOpen: false,
      selectedTemplate: undefined,
      isEditRegexpRouteTemplateModalOpen: false,
      channelFilterIdForEdit: undefined,
      isTemplateSettingsOpen: false,
      isAddingRoute: false,
      openRoutes: [],
    };
  }

  async componentDidMount() {
    const { query } = this.props;

    if (query?.template) {
      this.openEditTemplateModal(query.template, query.routeId && query.routeId);
    }

    await this.loadIntegration();
  }

  render() {
    const {
      isLoading,
      errorData,
      isEditTemplateModalOpen,
      selectedTemplate,
      isEditRegexpRouteTemplateModalOpen,
      channelFilterIdForEdit,
      isTemplateSettingsOpen,
    } = this.state;
    const {
      store: { alertReceiveChannelStore },
      query: { p },
      match: {
        params: { id },
      },
    } = this.props;

    const { isNotFoundError, isWrongTeamError } = errorData;

    const alertReceiveChannel = alertReceiveChannelStore.items[id];
    const templates = alertReceiveChannelStore.templates[id];

    if (isLoading && !isNotFoundError && !isWrongTeamError) {
      return (
        <div className={cx('root')}>
          <LoadingPlaceholder text="Loading Integration..." />
        </div>
      );
    }

    const integration = alertReceiveChannelStore.getIntegration(alertReceiveChannel);
    const alertReceiveChannelCounter = alertReceiveChannelStore.counters[id];
    const isLegacyIntegration = integration && (integration?.value as string).toLowerCase().startsWith('legacy_');
    const contactPoints = alertReceiveChannelStore.connectedContactPoints?.[alertReceiveChannel.id];

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
                  noContent
                  heading={undefined}
                  content={
                    <IntegrationTemplateList
                      alertReceiveChannelId={alertReceiveChannel.id}
                      alertReceiveChannelIsBasedOnAlertManager={alertReceiveChannel.is_based_on_alertmanager}
                      alertReceiveChannelAllowSourceBasedResolving={alertReceiveChannel.allow_source_based_resolving}
                      openEditTemplateModal={this.openEditTemplateModal}
                      templates={templates}
                    />
                  }
                />
              </Drawer>
            )}

            <div className={cx('integration__heading-container')}>
              <PluginLink query={{ page: 'integrations', p }} className={cx('back-arrow')}>
                <IconButton name="arrow-left" size="xl" />
              </PluginLink>
              <h2 className={cx('integration__name')}>
                <Emoji text={alertReceiveChannel.verbal_name} />
              </h2>
              <IntegrationActions
                alertReceiveChannel={alertReceiveChannel}
                changeIsTemplateSettingsOpen={() => this.setState({ isTemplateSettingsOpen: true })}
                isLegacyIntegration={isLegacyIntegration}
              />
            </div>

            <div className={cx('integration__subheading-container')}>
              {this.renderDeprecatedHeaderMaybe(integration, isLegacyIntegration)}

              {this.renderDescriptionMaybe(alertReceiveChannel)}

              {/* MobX seems to have issues updating contact points if we don't reference it here */}
              {!contactPoints?.length && this.renderContactPointsWarningMaybe(alertReceiveChannel)}

              <div className={cx('no-wrap')}>
                <IntegrationHeader
                  alertReceiveChannel={alertReceiveChannel}
                  alertReceiveChannelCounter={alertReceiveChannelCounter}
                  integration={integration}
                />
              </div>

              {alertReceiveChannel.description && (
                <div className={cx('integration__description-alert')}>
                  <Alert
                    title={
                      (
                        <div dangerouslySetInnerHTML={{ __html: sanitize(alertReceiveChannel.description) }}></div>
                      ) as any
                    }
                    severity="info"
                  />
                </div>
              )}
            </div>

            <IntegrationCollapsibleTreeView configElements={this.getConfigForTreeComponent(id, templates) as any} />

            {isEditTemplateModalOpen && (
              <IntegrationTemplate
                id={id}
                onHide={() => {
                  this.setState({
                    isEditTemplateModalOpen: undefined,
                  });
                  if (selectedTemplate?.name !== 'route_template') {
                    this.setState({ isTemplateSettingsOpen: true });
                  }
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

  renderDeprecatedHeaderMaybe(integration: SelectOption, isLegacyIntegration: boolean) {
    if (!isLegacyIntegration) {
      return null;
    }

    return (
      <div className="u-padding-top-md">
        <Alert
          severity="warning"
          title={
            (
              <VerticalGroup>
                <Text type="secondary">
                  We are introducing a new {getDisplayName()} integration. The existing integration is marked as Legacy
                  and will be migrated after 1 November 2023.
                </Text>
                <Text type="secondary">
                  To ensure a smooth transition you can migrate now using "Migrate" button in the menu on the right.
                </Text>
                <Text type="secondary">
                  Please, check{' '}
                  <a
                    href={`https://grafana.com/docs/oncall/latest/integrations/${getIntegrationName()}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    documentation
                  </a>{' '}
                  for more information.
                </Text>
              </VerticalGroup>
            ) as any
          }
        />
      </div>
    );

    function getDisplayName() {
      return integration.display_name.toString().replace('(Legacy) ', '');
    }

    function getIntegrationName() {
      return integration.value.toString().replace('legacy_', '').replace('_', '-');
    }
  }

  renderDescriptionMaybe(alertReceiveChannel: AlertReceiveChannel) {
    if (!alertReceiveChannel.description_short) {
      return null;
    }

    return (
      <Text type="secondary" className={cx('integration__description')}>
        {alertReceiveChannel.description_short}
      </Text>
    );
  }

  renderContactPointsWarningMaybe(alertReceiveChannel: AlertReceiveChannel) {
    if (IntegrationHelper.isGrafanaAlerting(alertReceiveChannel)) {
      return (
        <div className={cx('u-padding-top-md')}>
          <Alert
            title={
              (
                <Text type="primary">
                  Contact point connection required. Click{' '}
                  <a href="#" onClick={() => document.querySelector<HTMLElement>('#openContactPoint')?.click()}>
                    <Text type="link">here</Text>
                  </a>{' '}
                  to connect Contact point from Alerting.
                </Text>
              ) as any
            }
            className={cx('u-margin-bottom-none')}
            severity="error"
          />
        </div>
      );
    }

    return undefined;
  }

  getConfigForTreeComponent(id: string, templates: AlertTemplatesDTO[]) {
    const {
      store: { alertReceiveChannelStore },
    } = this.props;

    const alertReceiveChannel = alertReceiveChannelStore.items[id];

    return [
      IntegrationHelper.isGrafanaAlerting(alertReceiveChannel) && {
        isCollapsible: false,
        customIcon: 'grafana',
        canHoverIcon: false,
        collapsedView: null,
        expandedView: () => <IntegrationContactPoint id={id} />,
      },
      {
        isCollapsible: false,
        customIcon: 'plug',
        canHoverIcon: false,
        collapsedView: null,
        expandedView: () => <IntegrationHowToConnect id={id} />,
      },
      {
        customIcon: 'layer-group',
        isExpanded: false,
        isCollapsible: false,
        canHoverIcon: false,
        expandedView: () => (
          <IntegrationBlock
            noContent
            heading={
              <div className={cx('templates__outer-container')}>
                <Tag
                  color={getVar('--tag-secondary-transparent')}
                  border={getVar('--border-weak')}
                  className={cx('tag')}
                >
                  <Text type="primary" size="small" className={cx('radius')}>
                    Templates
                  </Text>
                </Tag>

                <div className={cx('templates__content')}>
                  <div className={cx('templates__container')}>
                    <div
                      className={cx('templates__item', 'templates__item--large')}
                      onClick={() => this.setState({ isTemplateSettingsOpen: true })}
                    >
                      <Text type="secondary" className={cx('templates__item-text')}>
                        Grouping:
                      </Text>
                      <Text type="primary">
                        {IntegrationHelper.truncateLine(templates?.['grouping_id_template'] || '')}
                      </Text>
                    </div>

                    <div
                      className={cx('templates__item', 'templates__item--large')}
                      onClick={() => this.setState({ isTemplateSettingsOpen: true })}
                    >
                      <Text type="secondary" className={cx('templates__item-text')}>
                        Autoresolve:
                      </Text>
                      <Text type="primary">
                        {IntegrationHelper.truncateLine(templates['resolve_condition_template'] || 'disabled')}
                      </Text>
                    </div>

                    <div
                      className={cx('templates__item', 'templates__item--large')}
                      onClick={() => this.setState({ isTemplateSettingsOpen: true })}
                    >
                      <Text type="secondary" className={cx('templates__item-text')}>
                        Other:
                      </Text>
                      <Text type="primary">Click to see more</Text>
                    </div>
                  </div>

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
        expandedView: () => (
          <div className={cx('routesSection')}>
            <VerticalGroup spacing="md">
              <Text type={'primary'} className={cx('routesSection__heading')}>
                Routes
              </Text>
              <HorizontalGroup>
                <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
                  <Button variant={'primary'} className={cx('routesSection__add')} onClick={this.handleAddNewRoute}>
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
    ].filter((opt) => opt);
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
            alert_receive_channel: id,
            filtering_term: NEW_ROUTE_DEFAULT,
            filtering_term_type: 1, // non-regex
          })
          .then(async (channelFilter: ChannelFilter) => {
            this.setState((prevState) => ({
              isAddingRoute: false,
              openRoutes: prevState.openRoutes.concat(channelFilter.id),
            }));
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

    const { openRoutes } = this.state;

    const templates = alertReceiveChannelStore.templates[id];
    const channelFilterIds = alertReceiveChannelStore.channelFilterIds[id];

    return channelFilterIds.map(
      (channelFilterId: ChannelFilter['id'], routeIndex: number) =>
        ({
          canHoverIcon: true,
          isCollapsible: true,
          isExpanded: openRoutes.indexOf(channelFilterId) > -1,
          onStateChange: (isChecked: boolean) => {
            const newOpenRoutes = [...openRoutes];
            this.setState({
              openRoutes: isChecked
                ? newOpenRoutes.concat(channelFilterId)
                : newOpenRoutes.filter((filterId) => filterId !== channelFilterId),
            });
          },
          collapsedView: (toggle) => (
            <CollapsedIntegrationRouteDisplay
              alertReceiveChannelId={id}
              channelFilterId={channelFilterId}
              routeIndex={routeIndex}
              toggle={toggle}
              openEditTemplateModal={this.openEditTemplateModal}
              onEditRegexpTemplate={this.handleEditRegexpRouteTemplate}
            />
          ),
          expandedView: () => (
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
        this.setState({
          isEditTemplateModalOpen: undefined,
        });
        LocationHelper.update({ template: undefined, routeId: undefined }, 'partial');
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
        this.setState({ isEditTemplateModalOpen: undefined });
        this.setState({ isTemplateSettingsOpen: true });
        LocationHelper.update({ template: undefined, routeId: undefined }, 'partial');
      })
      .catch((err) => {
        if (err.response?.data?.length > 0) {
          openErrorNotification(err.response.data);
        } else {
          openErrorNotification('Template is not valid. Please check your template and try again');
        }
      });
  };

  getTemplatesList = (): CascaderOption[] => INTEGRATION_TEMPLATES_LIST;

  openEditTemplateModal = (templateName, channelFilterId?: ChannelFilter['id']) => {
    if (templateForEdit[templateName]) {
      this.setState({
        isEditTemplateModalOpen: true,
        selectedTemplate: templateForEdit[templateName],
      });
    } else {
      openErrorNotification('Template can not be edited. Please contact support.');
    }

    if (channelFilterId) {
      this.setState({ channelFilterIdForEdit: channelFilterId });
    }
  };

  onRemovalFn = (id: AlertReceiveChannel['id']) => {
    const {
      store: { alertReceiveChannelStore },
      history,
    } = this.props;

    alertReceiveChannelStore.deleteAlertReceiveChannel(id).then(() => history.push(`${PLUGIN_ROOT}/integrations/`));
  };

  async loadIntegration() {
    const {
      store,
      store: { alertReceiveChannelStore },
      match: {
        params: { id },
      },
      history,
    } = this.props;

    const promises = [];

    if (!alertReceiveChannelStore.items[id]) {
      // See what happens if the request fails
      promises.push(alertReceiveChannelStore.loadItem(id));
    }

    if (!alertReceiveChannelStore.counters[id]) {
      promises.push(alertReceiveChannelStore.updateCounters());
    }

    if (!alertReceiveChannelStore.channelFilterIds[id]) {
      promises.push(alertReceiveChannelStore.updateChannelFilters(id));
    }

    promises.push(alertReceiveChannelStore.updateTemplates(id));

    promises.push(IntegrationHelper.fetchChatOps(store));

    // skip checking for grafana alerting so that we don't wait for the first request to complete
    // at the cost of getting a failed network request for all other types other than alerting
    promises.push(alertReceiveChannelStore.updateConnectedContactPoints(id).catch(noop));

    await Promise.all(promises)
      .catch(() => {
        if (!alertReceiveChannelStore.items[id]) {
          // failed fetching the integration (most likely it's not existent)
          history.push(`${PLUGIN_ROOT}/integrations`);
        }
      })
      .finally(() => this.setState({ isLoading: false }));
  }
}

interface IntegrationActionsProps {
  isLegacyIntegration: boolean;
  alertReceiveChannel: AlertReceiveChannel;
  changeIsTemplateSettingsOpen: () => void;
}

const IntegrationActions: React.FC<IntegrationActionsProps> = ({
  alertReceiveChannel,
  isLegacyIntegration,
  changeIsTemplateSettingsOpen,
}) => {
  const { alertReceiveChannelStore } = useStore();

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
  const [isHeartbeatFormOpen, setIsHeartbeatFormOpen] = useState(false);
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
        <IntegrationSendDemoAlertModal
          alertReceiveChannel={alertReceiveChannel}
          isOpen={isDemoModalOpen}
          onHideOrCancel={() => setIsDemoModalOpen(false)}
        />
      )}

      {isIntegrationSettingsOpen && (
        <IntegrationForm
          isTableView={false}
          onHide={() => setIsIntegrationSettingsOpen(false)}
          onSubmit={() => alertReceiveChannelStore.updateItem(alertReceiveChannel['id'])}
          id={alertReceiveChannel['id']}
        />
      )}

      {isHeartbeatFormOpen && (
        <IntegrationHeartbeatForm
          alertReceveChannelId={alertReceiveChannel['id']}
          onClose={() => setIsHeartbeatFormOpen(false)}
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
          data-testid="integration-settings-context-menu"
          renderMenuItems={() => (
            <div className={cx('integration__actionsList')} id="integration-menu-options">
              <div className={cx('integration__actionItem')} onClick={() => openIntegrationSettings()}>
                <Text type="primary">Integration Settings</Text>
              </div>

              {showHeartbeatSettings() && (
                <WithPermissionControlTooltip key="ok" userAction={UserActions.IntegrationsWrite}>
                  <div
                    className={cx('integration__actionItem')}
                    onClick={() => setIsHeartbeatFormOpen(true)}
                    data-testid="integration-heartbeat-settings"
                  >
                    Heartbeat Settings
                  </div>
                </WithPermissionControlTooltip>
              )}

              {!alertReceiveChannel.maintenance_till && (
                <WithPermissionControlTooltip userAction={UserActions.MaintenanceWrite}>
                  <div
                    className={cx('integration__actionItem')}
                    onClick={openStartMaintenance}
                    data-testid="integration-start-maintenance"
                  >
                    <Text type="primary">Start Maintenance</Text>
                  </div>
                </WithPermissionControlTooltip>
              )}

              <WithPermissionControlTooltip userAction={UserActions.MaintenanceWrite}>
                <div className={cx('integration__actionItem')} onClick={changeIsTemplateSettingsOpen}>
                  <Text type="primary">Edit Templates</Text>
                </div>
              </WithPermissionControlTooltip>

              {alertReceiveChannel.maintenance_till && (
                <WithPermissionControlTooltip userAction={UserActions.MaintenanceWrite}>
                  <div
                    className={cx('integration__actionItem')}
                    onClick={() => {
                      setConfirmModal({
                        isOpen: true,
                        confirmText: 'Stop',
                        dismissText: 'Cancel',
                        onConfirm: onStopMaintenance,
                        title: 'Stop Maintenance',
                        body: (
                          <Text type="primary">
                            Are you sure you want to stop the maintenance for{' '}
                            <Emoji text={alertReceiveChannel.verbal_name} /> ?
                          </Text>
                        ),
                      });
                    }}
                    data-testid="integration-stop-maintenance"
                  >
                    <Text type="primary">Stop Maintenance</Text>
                  </div>
                </WithPermissionControlTooltip>
              )}

              {isLegacyIntegration && (
                <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
                  <div
                    className={cx('integration__actionItem')}
                    onClick={() =>
                      setConfirmModal({
                        isOpen: true,
                        title: 'Migrate Integration?',
                        body: (
                          <VerticalGroup spacing="lg">
                            <Text type="primary">
                              Are you sure you want to migrate <Emoji text={alertReceiveChannel.verbal_name} /> ?
                            </Text>

                            <VerticalGroup spacing="xs">
                              <Text type="secondary">- Integration internal behaviour will be changed</Text>
                              <Text type="secondary">
                                - Integration URL will stay the same, so no need to change {getMigrationDisplayName()}{' '}
                                configuration
                              </Text>
                              <Text type="secondary">
                                - Integration templates will be reset to suit the new payload
                              </Text>
                              <Text type="secondary">- It is needed to adjust routes manually to the new payload</Text>
                            </VerticalGroup>
                          </VerticalGroup>
                        ),
                        onConfirm: onIntegrationMigrate,
                        dismissText: 'Cancel',
                        confirmText: 'Migrate',
                      })
                    }
                  >
                    Migrate
                  </div>
                </WithPermissionControlTooltip>
              )}

              <CopyToClipboard
                text={alertReceiveChannel.id}
                onCopy={() => openNotification('Integration ID is copied')}
              >
                <div className={cx('integration__actionItem')}>
                  <HorizontalGroup spacing={'xs'}>
                    <Icon name="copy" />

                    <Text type="primary">UID: {alertReceiveChannel.id}</Text>
                  </HorizontalGroup>
                </div>
              </CopyToClipboard>

              <div className={cx('thin-line-break')} />

              <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
                <div className={cx('integration__actionItem')}>
                  <div
                    onClick={() => {
                      setConfirmModal({
                        isOpen: true,
                        title: 'Delete Integration?',
                        body: (
                          <Text type="primary">
                            Are you sure you want to delete <Emoji text={alertReceiveChannel.verbal_name} /> ?
                          </Text>
                        ),
                        onConfirm: deleteIntegration,
                        dismissText: 'Cancel',
                        confirmText: 'Delete',
                      });
                    }}
                    className="u-width-100"
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
          {({ openMenu }) => <HamburgerMenu openMenu={openMenu} listBorder={2} listWidth={200} withBackground />}
        </WithContextMenu>
      </div>
    </>
  );

  function getMigrationDisplayName() {
    const name = alertReceiveChannel.integration.toLowerCase().replace('legacy_', '');
    switch (name) {
      case 'grafana_alerting':
        return 'Grafana Alerting';
      case 'alertmanager':
      default:
        return 'AlertManager';
    }
  }

  function onIntegrationMigrate() {
    alertReceiveChannelStore
      .migrateChannel(alertReceiveChannel.id)
      .then(() => {
        setConfirmModal(undefined);
        openNotification('Integration has been successfully migrated.');
      })
      .then(() =>
        Promise.all([
          alertReceiveChannelStore.updateItem(alertReceiveChannel.id),
          alertReceiveChannelStore.updateTemplates(alertReceiveChannel.id),
        ])
      )
      .catch(() => openErrorNotification('An error has occurred. Please try again.'));
  }

  function showHeartbeatSettings() {
    return alertReceiveChannel.is_available_for_integration_heartbeat;
  }

  function deleteIntegration() {
    alertReceiveChannelStore
      .deleteAlertReceiveChannel(alertReceiveChannel.id)
      .then(() => history.push(`${PLUGIN_ROOT}/integrations`))
      .then(() => openNotification('Integration has been succesfully deleted.'))
      .catch(() => openErrorNotification('An error has occurred. Please try again.'));
  }

  function openIntegrationSettings() {
    setIsIntegrationSettingsOpen(true);
  }

  function openStartMaintenance() {
    setMaintenanceData({ disabled: true, alert_receive_channel_id: alertReceiveChannel.id });
  }

  async function onStopMaintenance() {
    setConfirmModal(undefined);

    await alertReceiveChannelStore.stopMaintenanceMode(id);

    openNotification('Maintenance has been stopped');
    await alertReceiveChannelStore.updateItem(id);
  }
};

interface IntegrationHeaderProps {
  alertReceiveChannelCounter: AlertReceiveChannelCounters;
  alertReceiveChannel: AlertReceiveChannel;
  integration: SelectOption;
}

const IntegrationHeader: React.FC<IntegrationHeaderProps> = ({
  integration,
  alertReceiveChannelCounter,
  alertReceiveChannel,
}) => {
  const { grafanaTeamStore, heartbeatStore, alertReceiveChannelStore } = useStore();

  return (
    <div className={cx('headerTop')}>
      {alertReceiveChannelCounter && (
        <PluginLink
          className={cx('hover-button')}
          target="_blank"
          query={{ page: 'alert-groups', integration: alertReceiveChannel.id }}
        >
          <TooltipBadge
            borderType="primary"
            tooltipTitle={getAlertReceiveChannelCounterTooltip()}
            tooltipContent={undefined}
            text={alertReceiveChannelCounter?.alerts_count + '/' + alertReceiveChannelCounter?.alert_groups_count}
          />
        </PluginLink>
      )}

      <TooltipBadge
        borderType="success"
        icon="link"
        text={`${alertReceiveChannel.connected_escalations_chains_count}/${alertReceiveChannel.routes_count}`}
        tooltipTitle={
          alertReceiveChannel.connected_escalations_chains_count +
          ' connected escalation chain' +
          (alertReceiveChannel.connected_escalations_chains_count === 1 ? '' : 's') +
          ' in ' +
          alertReceiveChannel.routes_count +
          ' route' +
          (alertReceiveChannel.routes_count === 1 ? '' : 's')
        }
        tooltipContent={undefined}
      />

      {alertReceiveChannel.maintenance_till && (
        <TooltipBadge
          data-testid="maintenance-mode-remaining-time-tooltip"
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

      {renderHeartbeat(alertReceiveChannel)}

      <div style={{ display: 'flex', flexDirection: 'row', gap: '16px', marginLeft: '8px' }}>
        <div className={cx('headerTop__item')}>
          <Text type="secondary">Type:</Text>
          <HorizontalGroup spacing="xs">
            <IntegrationLogo scale={0.08} integration={integration} />
            <Text type="primary">{integration?.display_name}</Text>
          </HorizontalGroup>
        </div>
        <div className={cx('headerTop__item')}>
          <Text type="secondary">Team:</Text>
          <TeamName team={grafanaTeamStore.items[alertReceiveChannel.team]} />
        </div>
        <div className={cx('headerTop__item')}>
          <Text type="secondary">Created by:</Text>
          <UserDisplayWithAvatar id={alertReceiveChannel.author as any}></UserDisplayWithAvatar>
        </div>
      </div>
    </div>
  );

  function getAlertReceiveChannelCounterTooltip() {
    const alertReceiveChannelCounter = alertReceiveChannelStore.counters[alertReceiveChannel.id];

    return (
      alertReceiveChannelCounter?.alerts_count +
      ' alert' +
      (alertReceiveChannelCounter?.alerts_count === 1 ? '' : 's') +
      ' in ' +
      alertReceiveChannelCounter?.alert_groups_count +
      ' alert group' +
      (alertReceiveChannelCounter?.alert_groups_count === 1 ? '' : 's')
    );
  }

  function renderHeartbeat(alertReceiveChannel: AlertReceiveChannel) {
    const heartbeatId = alertReceiveChannelStore.alertReceiveChannelToHeartbeat[alertReceiveChannel.id];
    const heartbeat = heartbeatStore.items[heartbeatId];

    if (!alertReceiveChannel.is_available_for_integration_heartbeat || !heartbeat?.last_heartbeat_time_verbal) {
      return null;
    }

    const heartbeatStatus = Boolean(heartbeat?.status);

    return (
      <TooltipBadge
        data-testid="heartbeat-badge"
        text={undefined}
        className={cx('heartbeat-badge')}
        borderType={heartbeatStatus ? 'success' : 'danger'}
        customIcon={heartbeatStatus ? <HeartIcon /> : <HeartRedIcon />}
        tooltipTitle={`Last heartbeat: ${heartbeat?.last_heartbeat_time_verbal}`}
        tooltipContent={undefined}
      />
    );
  }
};

export default withRouter(withMobXProviderContext(Integration));
