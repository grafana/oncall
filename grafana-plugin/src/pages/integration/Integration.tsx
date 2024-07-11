import React, { useEffect, useState } from 'react';

import { LabelTag } from '@grafana/labels';
import {
  Button,
  HorizontalGroup,
  VerticalGroup,
  Icon,
  LoadingPlaceholder,
  IconButton,
  ConfirmModal,
  Drawer,
  Alert,
} from '@grafana/ui';
import cn from 'classnames/bind';
import { get } from 'lodash-es';
import { observer } from 'mobx-react';
import moment from 'moment-timezone';
import CopyToClipboard from 'react-copy-to-clipboard';
import Emoji from 'react-emoji-render';
import { RouteComponentProps, useHistory, withRouter } from 'react-router-dom';

import { getTemplatesForEdit } from 'components/AlertTemplates/AlertTemplatesForm.config';
import { TemplateForEdit } from 'components/AlertTemplates/CommonAlertTemplatesForm.config';
import { HamburgerContextMenu } from 'components/HamburgerContextMenu/HamburgerContextMenu';
import {
  IntegrationCollapsibleTreeView,
  IntegrationCollapsibleItem,
} from 'components/IntegrationCollapsibleTreeView/IntegrationCollapsibleTreeView';
import { IntegrationContactPoint } from 'components/IntegrationContactPoint/IntegrationContactPoint';
import { IntegrationHowToConnect } from 'components/IntegrationHowToConnect/IntegrationHowToConnect';
import { IntegrationLogoWithTitle } from 'components/IntegrationLogo/IntegrationLogoWithTitle';
import { IntegrationSendDemoAlertModal } from 'components/IntegrationSendDemoAlertModal/IntegrationSendDemoAlertModal';
import { IntegrationBlock } from 'components/Integrations/IntegrationBlock';
import { IntegrationTag } from 'components/Integrations/IntegrationTag';
import { PageErrorHandlingWrapper, PageBaseState } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper';
import { initErrorDataState } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper.helpers';
import { PluginLink } from 'components/PluginLink/PluginLink';
import { Tabs } from 'components/Tabs/Tabs';
import { Text } from 'components/Text/Text';
import { TooltipBadge } from 'components/TooltipBadge/TooltipBadge';
import { EditRegexpRouteTemplateModal } from 'containers/EditRegexpRouteTemplateModal/EditRegexpRouteTemplateModal';
import { CollapsedIntegrationRouteDisplay } from 'containers/IntegrationContainers/CollapsedIntegrationRouteDisplay/CollapsedIntegrationRouteDisplay';
import { ExpandedIntegrationRouteDisplay } from 'containers/IntegrationContainers/ExpandedIntegrationRouteDisplay/ExpandedIntegrationRouteDisplay';
import { IntegrationHeartbeatForm } from 'containers/IntegrationContainers/IntegrationHeartbeatForm/IntegrationHeartbeatForm';
import { IntegrationTemplateList } from 'containers/IntegrationContainers/IntegrationTemplatesList';
import { IntegrationFormContainer } from 'containers/IntegrationForm/IntegrationFormContainer';
import { IntegrationLabelsForm } from 'containers/IntegrationLabelsForm/IntegrationLabelsForm';
import { IntegrationTemplate } from 'containers/IntegrationTemplate/IntegrationTemplate';
import { MaintenanceForm } from 'containers/MaintenanceForm/MaintenanceForm';
import { CompleteServiceNowModal } from 'containers/ServiceNowConfigDrawer/CompleteServiceNowConfigModal';
import { ServiceNowConfigDrawer } from 'containers/ServiceNowConfigDrawer/ServiceNowConfigDrawer';
import { TeamName } from 'containers/TeamName/TeamName';
import { UserDisplayWithAvatar } from 'containers/UserDisplay/UserDisplayWithAvatar';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { HeartIcon, HeartRedIcon } from 'icons/Icons';
import { AlertReceiveChannelHelper } from 'models/alert_receive_channel/alert_receive_channel.helpers';
import { AlertReceiveChannelCounters } from 'models/alert_receive_channel/alert_receive_channel.types';
import { AlertTemplatesDTO } from 'models/alert_templates/alert_templates';
import { ChannelFilter } from 'models/channel_filter/channel_filter.types';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { IntegrationHelper, getIsBidirectionalIntegration } from 'pages/integration/Integration.helper';
import styles from 'pages/integration/Integration.module.scss';
import { AppFeature } from 'state/features';
import { PageProps, SelectOption, WithDrawerConfig, WithStoreProps } from 'state/types';
import { useStore } from 'state/useStore';
import { withMobXProviderContext } from 'state/withStore';
import { LocationHelper } from 'utils/LocationHelper';
import { UserActions } from 'utils/authorization/authorization';
import { GENERIC_ERROR, INTEGRATION_SERVICENOW, PLUGIN_ROOT } from 'utils/consts';
import { withDrawer } from 'utils/hoc';
import { useDrawer } from 'utils/hooks';
import { getItem, setItem } from 'utils/localStorage';
import { sanitize } from 'utils/sanitize';
import { openNotification, openErrorNotification } from 'utils/utils';

import { OutgoingTab } from './OutgoingTab/OutgoingTab';

const cx = cn.bind(styles);

interface IntegrationProps
  extends WithDrawerConfig<IntegrationDrawerKey>,
    WithStoreProps,
    PageProps,
    RouteComponentProps<{ id: string }> {}

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
class _IntegrationPage extends React.Component<IntegrationProps, IntegrationState> {
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

    await this.loadData();
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
      store,
      query,
      match: {
        params: { id },
      },
      drawerConfig,
    } = this.props;

    const { alertReceiveChannelStore } = store;

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

    const integration = AlertReceiveChannelHelper.getIntegrationSelectOption(
      alertReceiveChannelStore,
      alertReceiveChannel
    );
    const alertReceiveChannelCounter = alertReceiveChannelStore.counters[id];
    const isLegacyIntegration = integration && (integration?.value as string).toLowerCase().startsWith('legacy_');
    const contactPoints = alertReceiveChannelStore.connectedContactPoints?.[alertReceiveChannel.id];

    const incomingPart = (
      <>
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
            onUpdateRoute={(values, channelFilterId) => this.onUpdateRoutesCallback(values, channelFilterId, 1)}
            template={selectedTemplate}
            templateBody={
              selectedTemplate?.name === 'route_template'
                ? this.getRoutingTemplate(channelFilterIdForEdit)
                : templates[selectedTemplate?.name]
            }
            templates={templates}
          />
        )}
      </>
    );

    return (
      <PageErrorHandlingWrapper errorData={errorData} objectName="integration" pageName="Integration">
        {() => (
          <div className={cx('root')}>
            {isTemplateSettingsOpen && (
              <Drawer
                width="75%"
                scrollableContent
                title="Template Settings"
                subtitle="Set templates to interpret monitoring alerts and minimize noise. Group alerts, enable auto-resolution, customize visualizations and notifications by extracting data from alerts."
                onClose={() => this.setState({ isTemplateSettingsOpen: false })}
                closeOnMaskClick={false}
              >
                <IntegrationTemplateList
                  alertReceiveChannelId={alertReceiveChannel.id}
                  alertReceiveChannelIsBasedOnAlertManager={alertReceiveChannel.is_based_on_alertmanager}
                  alertReceiveChannelAllowSourceBasedResolving={alertReceiveChannel.allow_source_based_resolving}
                  openEditTemplateModal={this.openEditTemplateModal}
                  templates={templates}
                />
              </Drawer>
            )}

            <div className={cx('integration__heading-container')}>
              <PluginLink query={{ page: 'integrations', ...query }} className={cx('back-arrow')}>
                <IconButton aria-label="Go Back" name="arrow-left" size="xl" />
              </PluginLink>
              <h2 className={cx('integration__name')}>
                <Emoji text={alertReceiveChannel.verbal_name} />
              </h2>
              <IntegrationActions
                alertReceiveChannel={alertReceiveChannel}
                changeIsTemplateSettingsOpen={() => this.setState({ isTemplateSettingsOpen: true })}
                isLegacyIntegration={isLegacyIntegration}
                drawerConfig={drawerConfig}
              />
            </div>

            <div className={cx('integration__subheading-container')}>
              {this.renderDeprecatedHeaderMaybe(integration, isLegacyIntegration)}
              {this.renderAlertmanagerV2MigrationHeaderMaybe(alertReceiveChannel)}

              {this.renderDescriptionMaybe(alertReceiveChannel)}

              {/* MobX seems to have issues updating contact points if we don't reference it here */}
              {contactPoints && contactPoints.length === 0 && this.renderContactPointsWarningMaybe(alertReceiveChannel)}

              <div className={cx('no-wrap')}>
                <IntegrationHeader
                  alertReceiveChannel={alertReceiveChannel}
                  alertReceiveChannelCounter={alertReceiveChannelCounter}
                  integration={integration}
                  renderLabels={store.hasFeature(AppFeature.Labels)}
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

            {getIsBidirectionalIntegration(alertReceiveChannel) ? (
              <Tabs
                tabs={[
                  { label: 'Incoming', content: incomingPart },
                  {
                    label: 'Outgoing',
                    content: (
                      <OutgoingTab
                        openSnowConfigurationDrawer={() => drawerConfig.openDrawer(INTEGRATION_SERVICENOW)}
                      />
                    ),
                  },
                ]}
              />
            ) : (
              <>{incomingPart}</>
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
                  and will be migrated on 1st February 2024.
                </Text>
                <Text type="secondary">
                  To ensure a smooth transition you can migrate now using "Migrate" button in the menu on the right.
                </Text>
                <Text type="secondary">
                  Please check out the{' '}
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

  renderAlertmanagerV2MigrationHeaderMaybe(alertReceiveChannel: ApiSchemas['AlertReceiveChannel']) {
    if (!alertReceiveChannel.alertmanager_v2_migrated_at) {
      return null;
    }

    const alertID = `alertmanager_v2_alert_hidden_${alertReceiveChannel.id}`;
    if (getItem(alertID)) {
      return null;
    }
    const onAlertRemove = () => {
      setItem(alertID, true);
      this.forceUpdate();
    };

    const migratedAt = moment(alertReceiveChannel.alertmanager_v2_migrated_at).toString();
    const docsURL = `https://grafana.com/docs/oncall/latest/integrations/${alertReceiveChannel.integration.replace(
      '_',
      '-'
    )}`;

    return (
      <div className="u-padding-top-md">
        <Alert
          severity="warning"
          onRemove={onAlertRemove}
          title={
            (
              <VerticalGroup>
                <Text type="secondary">
                  This legacy integration was automatically migrated at {migratedAt}. It now relies on Alertmanager's
                  grouping and autoresolution mechanism.
                </Text>
                <Text type="secondary">Here are the steps you need to take to ensure a smooth transition:</Text>
                <Text type="secondary">
                  1. Check and adjust integration templates, as they were dropped back to default values during the
                  migration.
                </Text>
                <Text type="secondary">
                  2. Check and adjust integration routes so that they match the new payload shape.
                </Text>
                <Text type="secondary">
                  3. Check and adjust outgoing webhooks that use alerts from this integration so that they match the new
                  payload shape.
                </Text>
                <Text type="secondary">
                  Refer to{' '}
                  <a href={docsURL} target="_blank" rel="noreferrer">
                    <Text type="link">the docs</Text>
                  </a>{' '}
                  for more information.
                </Text>
              </VerticalGroup>
            ) as any
          }
        />
      </div>
    );
  }

  renderDescriptionMaybe(alertReceiveChannel: ApiSchemas['AlertReceiveChannel']) {
    if (!alertReceiveChannel.description_short) {
      return null;
    }

    return (
      <Text type="secondary" className={cx('integration__description')}>
        {alertReceiveChannel.description_short}
      </Text>
    );
  }

  renderContactPointsWarningMaybe(alertReceiveChannel: ApiSchemas['AlertReceiveChannel']) {
    if (IntegrationHelper.isSpecificIntegration(alertReceiveChannel, 'grafana_alerting')) {
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
    const contactPoints = alertReceiveChannelStore.connectedContactPoints[id];

    const isAlerting = IntegrationHelper.isSpecificIntegration(alertReceiveChannel, 'grafana_alerting');
    const isLegacyAlerting = IntegrationHelper.isSpecificIntegration(alertReceiveChannel, 'legacy_grafana_alerting');

    const configs: Array<IntegrationCollapsibleItem | IntegrationCollapsibleItem[]> = [
      (isAlerting || isLegacyAlerting) && {
        isHidden: isLegacyAlerting || contactPoints === null || contactPoints === undefined,
        isCollapsible: false,
        customIcon: 'grafana',
        canHoverIcon: false,
        collapsedView: null,
        startingElemPosition: '50%',
        expandedView: () => <IntegrationContactPoint id={id} />,
      },
      {
        isCollapsible: false,
        customIcon: 'plug',
        canHoverIcon: false,
        collapsedView: null,
        startingElemPosition: '50%',
        expandedView: () => <IntegrationHowToConnect id={id} />,
      },
      {
        customIcon: 'layer-group',
        isExpanded: false,
        isCollapsible: false,
        canHoverIcon: false,
        startingElemPosition: '50%',
        expandedView: () => (
          <IntegrationBlock
            noContent
            heading={
              <div className={cx('templates__outer-container')}>
                <IntegrationTag>Templates</IntegrationTag>

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
                        {IntegrationHelper.truncateLine(templates?.['resolve_condition_template'] || 'disabled')}
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
        customIcon: 'plus',
        isCollapsible: false,
        collapsedView: null,
        canHoverIcon: false,
        startingElemPosition: '40px',
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
                {this.state.isAddingRoute && (
                  <LoadingPlaceholder text="Loading..." className={cx('loadingPlaceholder')} />
                )}
              </HorizontalGroup>
            </VerticalGroup>
          </div>
        ),
      },
      this.renderRoutesFn() as IntegrationCollapsibleItem[],
    ];

    return configs.filter(Boolean);
  }

  getRoutingTemplate = (channelFilterId: ChannelFilter['id']) => {
    const {
      store: { alertReceiveChannelStore },
    } = this.props;

    return alertReceiveChannelStore.channelFilters[channelFilterId]?.filtering_term;
  };

  handleAddNewRoute = () => {
    const { alertReceiveChannelStore } = this.props.store;
    const {
      params: { id },
    } = this.props.match;

    this.setState(
      {
        isAddingRoute: true,
      },
      async () => {
        try {
          const channelFilter: ChannelFilter = await AlertReceiveChannelHelper.createChannelFilter({
            alert_receive_channel: id,
            filtering_term: NEW_ROUTE_DEFAULT,
            filtering_term_type: 1, // non-regex
          });
          await alertReceiveChannelStore.fetchChannelFilters(id);
          this.setState(
            (prevState) => ({
              isAddingRoute: false,
              openRoutes: prevState.openRoutes.concat(channelFilter.id),
            }),
            () => this.forceUpdate()
          );
          openNotification('A new route has been added');
        } catch (err) {
          const errors = get(err, 'response.data');
          if (errors?.non_field_errors) {
            openErrorNotification(errors.non_field_errors);
          }
        }
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

    const onRouteDelete = async (routeId: string) => {
      await alertReceiveChannelStore.deleteChannelFilter(routeId);
      this.forceUpdate();
      openNotification('Route has been deleted');
    };

    return (channelFilterIds || []).map(
      (channelFilterId: ChannelFilter['id'], routeIndex: number) =>
        ({
          canHoverIcon: true,
          isCollapsible: true,
          startingElemPosition: '50%',
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
              onItemMove={() => this.forceUpdate()}
              openEditTemplateModal={this.openEditTemplateModal}
              onEditRegexpTemplate={this.handleEditRegexpRouteTemplate}
              onRouteDelete={onRouteDelete}
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
              onItemMove={() => this.forceUpdate()}
              onRouteDelete={onRouteDelete}
            />
          ),
        } as IntegrationCollapsibleItem)
    ) as IntegrationCollapsibleItem[];
  };

  handleEditRegexpRouteTemplate = (channelFilterId) => {
    this.setState({ isEditRegexpRouteTemplateModalOpen: true, channelFilterIdForEdit: channelFilterId });
  };

  onUpdateRoutesCallback = async (
    { route_template }: { route_template: string },
    channelFilterId: ChannelFilter['id'],
    filteringTermType?: number
  ) => {
    const { alertReceiveChannelStore, escalationPolicyStore } = this.props.store;
    const {
      params: { id },
    } = this.props.match;

    try {
      const channelFilter: ChannelFilter = await alertReceiveChannelStore.saveChannelFilter(channelFilterId, {
        filtering_term: route_template,
        filtering_term_type: filteringTermType,
      });
      await alertReceiveChannelStore.fetchChannelFilters(id, true);
      escalationPolicyStore.updateEscalationPolicies(channelFilter.escalation_chain);
      this.setState({
        isEditTemplateModalOpen: undefined,
      });
      LocationHelper.update({ template: undefined, routeId: undefined }, 'partial');
    } catch (err) {
      const errors = get(err, 'response.data');
      if (errors?.non_field_errors) {
        openErrorNotification(errors.non_field_errors);
      }
    }
  };

  onUpdateTemplatesCallback = async (data) => {
    const {
      store,
      match: {
        params: { id },
      },
    } = this.props;

    try {
      await store.alertReceiveChannelStore.saveTemplates(id, data);
      openNotification('The Alert templates have been updated');
      this.setState({ isEditTemplateModalOpen: undefined });
      this.setState({ isTemplateSettingsOpen: true });
      LocationHelper.update({ template: undefined, routeId: undefined }, 'partial');
    } catch (err) {
      if (err.response?.data?.length > 0) {
        openErrorNotification(err.response.data);
      } else {
        openErrorNotification('Template is not valid. Please check your template and try again');
      }
    }
  };

  openEditTemplateModal = (templateName, channelFilterId?: ChannelFilter['id']) => {
    const { store } = this.props;

    const templateForEdit = getTemplatesForEdit(store.features);

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

  onRemovalFn = async (id: ApiSchemas['AlertReceiveChannel']['id']) => {
    await AlertReceiveChannelHelper.deleteAlertReceiveChannel(id);
    this.props.history.push(`${PLUGIN_ROOT}/integrations/`);
  };

  async loadData() {
    const {
      store: { alertReceiveChannelStore, msteamsChannelStore, hasFeature },
      match: {
        params: { id },
      },
      history,
    } = this.props;

    const promises: Array<Promise<void | { [key: string]: { alerts_count: number; alert_groups_count: number } }>> = [];

    const fetchItemAndLoadExtraData = async () => {
      await alertReceiveChannelStore.fetchItemById(id);
      await this.loadExtraData(id);
    };

    if (!alertReceiveChannelStore.items[id]) {
      promises.push(fetchItemAndLoadExtraData());
    } else {
      promises.push(this.loadExtraData(id));
    }

    if (!alertReceiveChannelStore.channelFilterIds[id]) {
      promises.push(alertReceiveChannelStore.fetchChannelFilters(id));
    }

    promises.push(alertReceiveChannelStore.fetchTemplates(id));
    if (hasFeature(AppFeature.MsTeams)) {
      promises.push(msteamsChannelStore.updateMSTeamsChannels());
    }
    promises.push(alertReceiveChannelStore.fetchCountersForIntegration(id));

    try {
      await Promise.all(promises);
    } catch (_err) {
      if (!alertReceiveChannelStore.items[id]) {
        // failed fetching the integration (most likely it's not existent)
        history.push(`${PLUGIN_ROOT}/integrations`);
      }
    } finally {
      this.setState({ isLoading: false });
    }
  }

  async loadExtraData(id: ApiSchemas['AlertReceiveChannel']['id']) {
    const { alertReceiveChannelStore } = this.props.store;

    if (IntegrationHelper.isSpecificIntegration(alertReceiveChannelStore.items[id], 'grafana_alerting')) {
      // this will be delayed and not awaitable so that we don't delay the whole page load
      return await alertReceiveChannelStore.fetchConnectedContactPoints(id);
    }

    return Promise.resolve();
  }
}

interface IntegrationActionsProps {
  isLegacyIntegration: boolean;
  alertReceiveChannel: ApiSchemas['AlertReceiveChannel'];
  changeIsTemplateSettingsOpen: () => void;
  drawerConfig: ReturnType<typeof useDrawer<IntegrationDrawerKey>>;
}

type IntegrationDrawerKey = typeof INTEGRATION_SERVICENOW | 'completeConfig';

const IntegrationActions: React.FC<IntegrationActionsProps> = ({
  alertReceiveChannel,
  isLegacyIntegration,
  changeIsTemplateSettingsOpen,
  drawerConfig,
}) => {
  const store = useStore();
  const { alertReceiveChannelStore } = store;

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

  const [isCompleteServiceNowConfigOpen, setIsCompleteServiceNowConfigOpen] = useState(false);
  const [isIntegrationSettingsOpen, setIsIntegrationSettingsOpen] = useState(false);
  const [isLabelsFormOpen, setLabelsFormOpen] = useState(false);
  const [isHeartbeatFormOpen, setIsHeartbeatFormOpen] = useState(false);
  const [isDemoModalOpen, setIsDemoModalOpen] = useState(false);
  const [maintenanceData, setMaintenanceData] = useState<{
    alert_receive_channel_id: ApiSchemas['AlertReceiveChannel']['id'];
  }>(undefined);

  const { closeDrawer, openDrawer, getIsDrawerOpened } = drawerConfig;

  const { id } = alertReceiveChannel;

  useEffect(() => {
    /* ServiceNow Only */
    openServiceNowCompleteConfigurationDrawer();
  }, []);

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

      {getIsDrawerOpened(INTEGRATION_SERVICENOW) && <ServiceNowConfigDrawer onHide={closeDrawer} />}

      {isCompleteServiceNowConfigOpen && (
        <CompleteServiceNowModal onHide={() => setIsCompleteServiceNowConfigOpen(false)} />
      )}

      {isIntegrationSettingsOpen && (
        <IntegrationFormContainer
          isTableView={false}
          onHide={() => setIsIntegrationSettingsOpen(false)}
          onSubmit={async () => {
            await alertReceiveChannelStore.fetchItemById(alertReceiveChannel.id);
          }}
          id={alertReceiveChannel['id']}
          navigateToAlertGroupLabels={(_id: ApiSchemas['AlertReceiveChannel']['id']) => {
            setIsIntegrationSettingsOpen(false);
            setLabelsFormOpen(true);
          }}
        />
      )}

      {isLabelsFormOpen && (
        <IntegrationLabelsForm
          onHide={() => {
            setLabelsFormOpen(false);
          }}
          onSubmit={() => alertReceiveChannelStore.fetchItemById(alertReceiveChannel.id)}
          id={alertReceiveChannel['id']}
          onOpenIntegrationSettings={() => {
            setIsIntegrationSettingsOpen(true);
          }}
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
          onUpdate={() => alertReceiveChannelStore.fetchItemById(alertReceiveChannel.id)}
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

        <div data-testid="integration-settings-context-menu-wrapper">
          <HamburgerContextMenu
            items={[
              {
                onClick: openIntegrationSettings,
                label: 'Integration Settings',
              },
              {
                label: 'ServiceNow configuration',
                hidden: !getIsBidirectionalIntegration(alertReceiveChannel),
                onClick: () => openDrawer(INTEGRATION_SERVICENOW),
              },
              {
                onClick: openLabelsForm,
                hidden: !store.hasFeature(AppFeature.Labels),
                label: 'Alert group labeling',
                requiredPermission: UserActions.IntegrationsWrite,
              },
              {
                onClick: () => setIsHeartbeatFormOpen(true),
                hidden: !showHeartbeatSettings(),
                label: <div data-testid="integration-heartbeat-settings">Heartbeat Settings</div>,
                requiredPermission: UserActions.IntegrationsWrite,
              },
              {
                onClick: openStartMaintenance,
                hidden: Boolean(alertReceiveChannel.maintenance_till),
                label: 'Start Maintenance',
                requiredPermission: UserActions.MaintenanceWrite,
              },
              {
                onClick: changeIsTemplateSettingsOpen,
                label: 'Edit Templates',
                requiredPermission: UserActions.MaintenanceWrite,
              },
              {
                onClick: () => {
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
                },
                hidden: !alertReceiveChannel.maintenance_till,
                label: 'Stop Maintenance',
                requiredPermission: UserActions.MaintenanceWrite,
              },
              {
                onClick: () =>
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
                          <Text type="secondary">- Integration templates will be reset to suit the new payload</Text>
                          <Text type="secondary">- It is needed to adjust routes manually to the new payload</Text>
                        </VerticalGroup>
                      </VerticalGroup>
                    ),
                    onConfirm: onIntegrationMigrate,
                    dismissText: 'Cancel',
                    confirmText: 'Migrate',
                  }),
                hidden: !isLegacyIntegration,
                label: 'Migrate',
                requiredPermission: UserActions.IntegrationsWrite,
              },
              {
                label: (
                  <CopyToClipboard
                    text={alertReceiveChannel.id}
                    onCopy={() => openNotification('Integration ID is copied')}
                  >
                    <div>
                      <HorizontalGroup spacing={'xs'}>
                        <Icon name="copy" />
                        <Text type="primary">UID: {alertReceiveChannel.id}</Text>
                      </HorizontalGroup>
                    </div>
                  </CopyToClipboard>
                ),
              },
              {
                onClick: () => {
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
                },
                hidden: !alertReceiveChannel.allow_delete,
                label: (
                  <Text type="danger">
                    <HorizontalGroup spacing={'xs'}>
                      <Icon name="trash-alt" />
                      <span>Delete Integration</span>
                    </HorizontalGroup>
                  </Text>
                ),
                requiredPermission: UserActions.IntegrationsWrite,
              },
            ]}
          />
        </div>
      </div>
    </>
  );

  function openServiceNowCompleteConfigurationDrawer() {
    const isServiceNow = getIsBidirectionalIntegration(alertReceiveChannel);
    const isConfigured = alertReceiveChannel.additional_settings?.is_configured;
    if (isServiceNow && !isConfigured) {
      setIsCompleteServiceNowConfigOpen(true);
    }
  }

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

  async function onIntegrationMigrate() {
    try {
      await AlertReceiveChannelHelper.migrateChannel(alertReceiveChannel.id);
      setConfirmModal(undefined);
      openNotification('Integration has been successfully migrated.');
      await Promise.all([
        alertReceiveChannelStore.fetchItemById(alertReceiveChannel.id),
        alertReceiveChannelStore.fetchTemplates(alertReceiveChannel.id),
      ]);
    } catch (_err) {
      openErrorNotification(GENERIC_ERROR);
    }
  }

  function showHeartbeatSettings() {
    return alertReceiveChannel.is_available_for_integration_heartbeat;
  }

  async function deleteIntegration() {
    try {
      await AlertReceiveChannelHelper.deleteAlertReceiveChannel(alertReceiveChannel.id);
      history.push(`${PLUGIN_ROOT}/integrations`);
      openNotification('Integration has been succesfully deleted.');
    } catch (_err) {
      openErrorNotification(GENERIC_ERROR);
    }
  }

  function openIntegrationSettings() {
    setIsIntegrationSettingsOpen(true);
  }

  function openLabelsForm() {
    setLabelsFormOpen(true);
  }

  function openStartMaintenance() {
    setMaintenanceData({ alert_receive_channel_id: alertReceiveChannel.id });
  }

  async function onStopMaintenance() {
    setConfirmModal(undefined);

    await AlertReceiveChannelHelper.stopMaintenanceMode(id);

    openNotification('Maintenance has been stopped');
    await alertReceiveChannelStore.fetchItemById(id);
  }
};

interface IntegrationHeaderProps {
  alertReceiveChannelCounter: AlertReceiveChannelCounters;
  alertReceiveChannel: ApiSchemas['AlertReceiveChannel'];
  integration: SelectOption;
  renderLabels: boolean;
}

const IntegrationHeader: React.FC<IntegrationHeaderProps> = ({
  integration,
  alertReceiveChannelCounter,
  alertReceiveChannel,
  renderLabels,
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

      {Boolean(renderLabels && alertReceiveChannel.labels.length) && (
        <TooltipBadge
          borderType="secondary"
          icon="tag-alt"
          addPadding
          text={alertReceiveChannel.labels.length}
          tooltipContent={
            <VerticalGroup spacing="sm">
              {alertReceiveChannel.labels.map((label) => (
                <LabelTag label={label.key.name} value={label.value.name} key={label.key.id} />
              ))}
            </VerticalGroup>
          }
        />
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
          testId="maintenance-mode-remaining-time-tooltip"
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
          <IntegrationLogoWithTitle integration={integration} />
        </div>
        <div className={cx('headerTop__item')}>
          <Text type="secondary">Team:</Text>
          <TeamName team={grafanaTeamStore.items[alertReceiveChannel.team]} />
        </div>
        {alertReceiveChannel.author && (
          <div className={cx('headerTop__item')}>
            <Text type="secondary">Created by:</Text>
            <UserDisplayWithAvatar id={alertReceiveChannel.author as any}></UserDisplayWithAvatar>
          </div>
        )}
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

  function renderHeartbeat(alertReceiveChannel: ApiSchemas['AlertReceiveChannel']) {
    const heartbeatId = alertReceiveChannelStore.alertReceiveChannelToHeartbeat[alertReceiveChannel.id];
    const heartbeat = heartbeatStore.items[heartbeatId];

    if (!alertReceiveChannel.is_available_for_integration_heartbeat || !heartbeat?.last_heartbeat_time_verbal) {
      return null;
    }

    const heartbeatStatus = Boolean(heartbeat?.status);

    return (
      <TooltipBadge
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

export const IntegrationPage = withRouter(withMobXProviderContext(withDrawer<IntegrationDrawerKey>(_IntegrationPage)));
