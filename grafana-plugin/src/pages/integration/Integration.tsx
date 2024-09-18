import React from 'react';

import { css, cx } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { LabelTag } from '@grafana/labels';
import {
  Button,
  Stack,
  LoadingPlaceholder,
  IconButton,
  Drawer,
  Alert,
  withTheme2,
  Themeable2,
  useStyles2,
} from '@grafana/ui';
import { sanitize } from 'dompurify';
import { LocationHelper } from 'helpers/LocationHelper';
import { UserActions } from 'helpers/authorization/authorization';
import { INTEGRATION_SERVICENOW, StackSize, PLUGIN_ROOT } from 'helpers/consts';
import { openNotification, openErrorNotification } from 'helpers/helpers';
import { PropsWithRouter, withRouter, withDrawer } from 'helpers/hoc';
import { getItem, setItem } from 'helpers/localStorage';
import { get } from 'lodash-es';
import { observer } from 'mobx-react';
import moment from 'moment-timezone';
import Emoji from 'react-emoji-render';
import { getUtilStyles } from 'styles/utils.styles';

import { getTemplatesForEdit } from 'components/AlertTemplates/AlertTemplatesForm.config';
import { TemplateForEdit } from 'components/AlertTemplates/CommonAlertTemplatesForm.config';
import { CollapsibleTreeView, CollapsibleItem } from 'components/CollapsibleTreeView/CollapsibleTreeView';
import { IntegrationContactPoint } from 'components/IntegrationContactPoint/IntegrationContactPoint';
import { IntegrationHowToConnect } from 'components/IntegrationHowToConnect/IntegrationHowToConnect';
import { IntegrationLogoWithTitle } from 'components/IntegrationLogo/IntegrationLogoWithTitle';
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
import { IntegrationTemplateList } from 'containers/IntegrationContainers/IntegrationTemplatesList';
import { IntegrationTemplate } from 'containers/IntegrationTemplate/IntegrationTemplate';
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
import { AppFeature } from 'state/features';
import { PageProps, SelectOption, WithDrawerConfig, WithStoreProps } from 'state/types';
import { useStore } from 'state/useStore';
import { withMobXProviderContext } from 'state/withStore';

import { getIntegrationStyles } from './Integration.styles';
import { IntegrationActions } from './IntegrationActions';
import { OutgoingTab } from './OutgoingTab/OutgoingTab';

export type IntegrationDrawerKey = typeof INTEGRATION_SERVICENOW | 'completeConfig';

interface RouteProps {
  id: string;
}

interface IntegrationProps
  extends WithDrawerConfig<IntegrationDrawerKey>,
    WithStoreProps,
    PageProps,
    PropsWithRouter<RouteProps>,
    Themeable2 {
  theme: GrafanaTheme2;
}

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
      router: {
        params: { id },
      },
      drawerConfig,
      theme,
    } = this.props;

    const { alertReceiveChannelStore } = store;

    const { isNotFoundError, isWrongTeamError } = errorData;

    const alertReceiveChannel = alertReceiveChannelStore.items[id];
    const templates = alertReceiveChannelStore.templates[id];

    if (isLoading && !isNotFoundError && !isWrongTeamError) {
      return (
        <div>
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
    const styles = getIntegrationStyles(theme);

    const incomingPart = (
      <>
        <CollapsibleTreeView configElements={this.getConfigForTreeComponent(id, templates) as any} />
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
          <div>
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

            <div className={styles.integrationHeadingContainer}>
              <PluginLink query={{ page: 'integrations', ...query }} className={styles.backArrow}>
                <IconButton aria-label="Go Back" name="arrow-left" size="xl" />
              </PluginLink>
              <h2 className={styles.integrationName}>
                <Emoji text={alertReceiveChannel.verbal_name} />
              </h2>
              <IntegrationActions
                alertReceiveChannel={alertReceiveChannel}
                changeIsTemplateSettingsOpen={() => this.setState({ isTemplateSettingsOpen: true })}
                isLegacyIntegration={isLegacyIntegration}
                drawerConfig={drawerConfig}
              />
            </div>

            <div className={styles.integrationSubHeadingContainer}>
              {this.renderDeprecatedHeaderMaybe(integration, isLegacyIntegration)}
              {this.renderAlertmanagerV2MigrationHeaderMaybe(alertReceiveChannel)}

              {this.renderDescriptionMaybe(alertReceiveChannel)}

              {/* MobX seems to have issues updating contact points if we don't reference it here */}
              {contactPoints && contactPoints.length === 0 && this.renderContactPointsWarningMaybe(alertReceiveChannel)}

              <div className={styles.noWrap}>
                <IntegrationHeader
                  alertReceiveChannel={alertReceiveChannel}
                  alertReceiveChannelCounter={alertReceiveChannelCounter}
                  integration={integration}
                  renderLabels={store.hasFeature(AppFeature.Labels)}
                />
              </div>

              {alertReceiveChannel.description && (
                <div className={styles.integrationDescriptionAlert}>
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
      <div
        className={css`
          padding-top: 12px;
        `}
      >
        <Alert
          severity="warning"
          title={
            (
              <Stack direction="column">
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
              </Stack>
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
      <div
        className={css`
          padding-top: 12px;
        `}
      >
        <Alert
          severity="warning"
          onRemove={onAlertRemove}
          title={
            (
              <Stack direction="column">
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
              </Stack>
            ) as any
          }
        />
      </div>
    );
  }

  renderDescriptionMaybe(alertReceiveChannel: ApiSchemas['AlertReceiveChannel']) {
    const styles = getIntegrationStyles(this.props.theme);

    if (!alertReceiveChannel.description_short) {
      return null;
    }

    return (
      <Text type="secondary" className={styles.integrationDescription}>
        {alertReceiveChannel.description_short}
      </Text>
    );
  }

  renderContactPointsWarningMaybe(alertReceiveChannel: ApiSchemas['AlertReceiveChannel']) {
    if (IntegrationHelper.isSpecificIntegration(alertReceiveChannel, 'grafana_alerting')) {
      return (
        <div
          className={css`
            padding-top: 12px;
          `}
        >
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
            className={css`
              margin-bottom: none;
            `}
            severity="error"
          />
        </div>
      );
    }

    return undefined;
  }

  getConfigForTreeComponent(id: string, templates: AlertTemplatesDTO[]) {
    const {
      theme,
      store: { alertReceiveChannelStore },
    } = this.props;

    const alertReceiveChannel = alertReceiveChannelStore.items[id];
    const contactPoints = alertReceiveChannelStore.connectedContactPoints[id];

    const isAlerting = IntegrationHelper.isSpecificIntegration(alertReceiveChannel, 'grafana_alerting');
    const isLegacyAlerting = IntegrationHelper.isSpecificIntegration(alertReceiveChannel, 'legacy_grafana_alerting');
    const styles = getIntegrationStyles(theme);
    const utilStyles = getUtilStyles(theme);

    const configs: Array<CollapsibleItem | CollapsibleItem[]> = [
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
              <div className={styles.templatesOuterContainer}>
                <IntegrationTag>Templates</IntegrationTag>

                <div className={styles.templatesContent}>
                  <div className={cx(styles.templatesContainer)}>
                    <div
                      className={cx(styles.templatesItem, styles.templatesItemLarge)}
                      onClick={() => this.setState({ isTemplateSettingsOpen: true })}
                    >
                      <Text type="secondary" className={styles.templatesItemText}>
                        Grouping:
                      </Text>
                      <Text type="primary">
                        {IntegrationHelper.truncateLine(templates?.['grouping_id_template'] || '')}
                      </Text>
                    </div>

                    <div
                      className={cx(styles.templatesItem, styles.templatesItemLarge)}
                      onClick={() => this.setState({ isTemplateSettingsOpen: true })}
                    >
                      <Text type="secondary" className={styles.templatesItemText}>
                        Autoresolve:
                      </Text>
                      <Text type="primary">
                        {IntegrationHelper.truncateLine(templates?.['resolve_condition_template'] || 'disabled')}
                      </Text>
                    </div>

                    <div
                      className={cx(styles.templatesItem, styles.templatesItemLarge)}
                      onClick={() => this.setState({ isTemplateSettingsOpen: true })}
                    >
                      <Text type="secondary" className={cx(styles.templatesItemText)}>
                        Other:
                      </Text>
                      <Text type="primary">Click to see more</Text>
                    </div>
                  </div>

                  <div className={styles.templatesEdit}>
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
          <div>
            <Stack direction="column" gap={StackSize.md}>
              <Text type={'primary'} className={styles.routesSectionHeading}>
                Routes
              </Text>
              <Stack>
                <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
                  <Button variant={'primary'} onClick={this.handleAddNewRoute}>
                    Add route
                  </Button>
                </WithPermissionControlTooltip>
                {this.state.isAddingRoute && (
                  <LoadingPlaceholder text="Loading..." className={utilStyles.loadingPlaceholder} />
                )}
              </Stack>
            </Stack>
          </div>
        ),
      },
      this.renderRoutesFn() as CollapsibleItem[],
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
    const {
      store: { alertReceiveChannelStore },
      router: {
        params: { id },
      },
    } = this.props;

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

  renderRoutesFn = (): CollapsibleItem[] => {
    const {
      store: { alertReceiveChannelStore },
      router: {
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
              key={`${channelFilterId}_${routeIndex}`} // Key is required
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
              key={`${channelFilterId}_${routeIndex}`} // Key is required
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
        } as CollapsibleItem)
    ) as CollapsibleItem[];
  };

  handleEditRegexpRouteTemplate = (channelFilterId) => {
    this.setState({ isEditRegexpRouteTemplateModalOpen: true, channelFilterIdForEdit: channelFilterId });
  };

  onUpdateRoutesCallback = async (
    { route_template }: { route_template: string },
    channelFilterId: ChannelFilter['id'],
    filteringTermType?: number
  ) => {
    const {
      store: { alertReceiveChannelStore, escalationPolicyStore },
      router: {
        params: { id },
      },
    } = this.props;

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
      router: {
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
    const {
      router: { navigate },
    } = this.props;
    await AlertReceiveChannelHelper.deleteAlertReceiveChannel(id);
    navigate(`${PLUGIN_ROOT}/integrations/`);
  };

  async loadData() {
    const {
      store: { alertReceiveChannelStore, msteamsChannelStore, hasFeature },
      router: {
        navigate,
        params: { id },
      },
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
        navigate(`${PLUGIN_ROOT}/integrations`);
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
  const styles = useStyles2(getIntegrationStyles);

  return (
    <div className={styles.headerTop}>
      {alertReceiveChannelCounter && (
        <PluginLink target="_blank" query={{ page: 'alert-groups', integration: alertReceiveChannel.id }}>
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
            <Stack direction="column" gap={StackSize.sm}>
              {alertReceiveChannel.labels.map((label) => (
                <LabelTag label={label.key.name} value={label.value.name} key={label.key.id} />
              ))}
            </Stack>
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
        <div className={styles.headerTopItem}>
          <Text type="secondary">Type:</Text>
          <IntegrationLogoWithTitle integration={integration} />
        </div>
        <div className={styles.headerTopItem}>
          <Text type="secondary">Team:</Text>
          <TeamName team={grafanaTeamStore.items[alertReceiveChannel.team]} />
        </div>
        {alertReceiveChannel.author && (
          <div className={styles.headerTopItem}>
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
        className={css`
          padding: 4px 8px;
        `}
        borderType={heartbeatStatus ? 'success' : 'danger'}
        customIcon={heartbeatStatus ? <HeartIcon /> : <HeartRedIcon />}
        tooltipTitle={`Last heartbeat: ${heartbeat?.last_heartbeat_time_verbal}`}
        tooltipContent={undefined}
      />
    );
  }
};

export const IntegrationPage = withRouter<
  RouteProps,
  Omit<IntegrationProps, 'store' | 'meta' | 'theme' | 'drawerConfig'>
>(withMobXProviderContext(withTheme2(withDrawer<IntegrationDrawerKey>(_IntegrationPage))));
