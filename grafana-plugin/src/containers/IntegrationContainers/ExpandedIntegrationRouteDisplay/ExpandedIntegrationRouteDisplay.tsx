import React, { useEffect, useReducer, useState } from 'react';

import { SelectableValue } from '@grafana/data';
import {
  Button,
  HorizontalGroup,
  VerticalGroup,
  Icon,
  Tooltip,
  ConfirmModal,
  LoadingPlaceholder,
  Select,
  Alert,
} from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import CopyToClipboard from 'react-copy-to-clipboard';

import { HamburgerMenuIcon } from 'components/HamburgerMenuIcon/HamburgerMenuIcon';
import {
  IntegrationCollapsibleTreeView,
  IntegrationCollapsibleItem,
} from 'components/IntegrationCollapsibleTreeView/IntegrationCollapsibleTreeView';
import { IntegrationBlock } from 'components/Integrations/IntegrationBlock';
import { MonacoEditor } from 'components/MonacoEditor/MonacoEditor';
import { MONACO_READONLY_CONFIG } from 'components/MonacoEditor/MonacoEditor.config';
import { PluginLink } from 'components/PluginLink/PluginLink';
import { Text } from 'components/Text/Text';
import { TooltipBadge } from 'components/TooltipBadge/TooltipBadge';
import { WithContextMenu } from 'components/WithContextMenu/WithContextMenu';
import { ChatOpsConnectors } from 'containers/AlertRules/AlertRules';
import { EscalationChainSteps } from 'containers/EscalationChainSteps/EscalationChainSteps';
import styles from 'containers/IntegrationContainers/ExpandedIntegrationRouteDisplay/ExpandedIntegrationRouteDisplay.module.scss';
import { TeamName } from 'containers/TeamName/TeamName';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { AlertTemplatesDTO } from 'models/alert_templates/alert_templates';
import { ChannelFilter } from 'models/channel_filter/channel_filter.types';
import { EscalationChain } from 'models/escalation_chain/escalation_chain.types';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { CommonIntegrationHelper } from 'pages/integration/CommonIntegration.helper';
import { IntegrationHelper } from 'pages/integration/Integration.helper';
import { MONACO_INPUT_HEIGHT_SMALL } from 'pages/integration/IntegrationCommon.config';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization/authorization';
import { openNotification } from 'utils/utils';

const cx = cn.bind(styles);

interface ExpandedIntegrationRouteDisplayProps {
  alertReceiveChannelId: ApiSchemas['AlertReceiveChannel']['id'];
  channelFilterId: ChannelFilter['id'];
  routeIndex: number;
  templates: AlertTemplatesDTO[];
  openEditTemplateModal: (templateName: string | string[], channelFilterId?: ChannelFilter['id']) => void;
  onEditRegexpTemplate: (channelFilterId: ChannelFilter['id']) => void;
  onRouteDelete: (routeId: string) => void;
  onItemMove: () => void;
}

interface ExpandedIntegrationRouteDisplayState {
  isEscalationCollapsed: boolean;
  isRefreshingEscalationChains: boolean;
  routeIdForDeletion: string;
}

export const ExpandedIntegrationRouteDisplay: React.FC<ExpandedIntegrationRouteDisplayProps> = observer(
  ({
    alertReceiveChannelId,
    channelFilterId,
    templates,
    routeIndex,
    openEditTemplateModal,
    onEditRegexpTemplate,
    onRouteDelete,
    onItemMove,
  }) => {
    const store = useStore();
    const {
      telegramChannelStore,
      escalationPolicyStore,
      escalationChainStore,
      alertReceiveChannelStore,
      grafanaTeamStore,
    } = store;

    const [isLoading, setIsLoading] = useState(false);

    const [{ isEscalationCollapsed, isRefreshingEscalationChains, routeIdForDeletion }, setState] = useReducer(
      (state: ExpandedIntegrationRouteDisplayState, newState: Partial<ExpandedIntegrationRouteDisplayState>) => ({
        ...state,
        ...newState,
      }),
      {
        isEscalationCollapsed: true,
        isRefreshingEscalationChains: false,
        routeIdForDeletion: undefined,
      }
    );

    useEffect(() => {
      setIsLoading(true);
      (async () => {
        await Promise.all([escalationChainStore.updateItems(), telegramChannelStore.updateTelegramChannels()]);
        setIsLoading(false);
      })();
    }, []);

    const channelFilter = alertReceiveChannelStore.channelFilters[channelFilterId];
    if (!channelFilter) {
      return null;
    }

    const escalationChainRedirectObj: any = { page: 'escalations', id: channelFilter.escalation_chain || 'new' };
    const channelFilterIds = alertReceiveChannelStore.channelFilterIds[alertReceiveChannelId];
    const isDefault = CommonIntegrationHelper.getRouteConditionWording(channelFilterIds, routeIndex) === 'Default';
    const channelFilterTemplate = channelFilter.filtering_term
      ? IntegrationHelper.getFilteredTemplate(channelFilter.filtering_term, false)
      : '{# Add Routing Template, e.g. {{ payload.severity == "critical" }} #}';

    if (isLoading) {
      return <LoadingPlaceholder text="Loading..." />;
    }

    const escChainDisplayName = escalationChainStore.items[channelFilter.escalation_chain]?.name;
    const getTreeViewElements = () => {
      const configs: IntegrationCollapsibleItem[] = [
        {
          isHidden: false,
          isCollapsible: false,
          isExpanded: false,
          isTextIcon: true,
          collapsedView: null,
          canHoverIcon: false,
          expandedView: () => (
            <div className={cx('adjust-element-padding')}>
              {isDefault ? (
                <div className={cx('default-route-view')}>
                  <Text customTag="h6" type="primary">
                    All unmatched alerts are directed to this route, grouped using the Grouping Template, sent to
                    messengers, and trigger the escalation chain
                  </Text>
                </div>
              ) : (
                <VerticalGroup spacing="sm">
                  <Text customTag="h6" type="primary">
                    Use routing template
                  </Text>

                  <HorizontalGroup spacing="xs">
                    <div className={cx('input', 'input--align')}>
                      <MonacoEditor
                        value={channelFilterTemplate}
                        disabled={true}
                        height={MONACO_INPUT_HEIGHT_SMALL}
                        data={templates}
                        showLineNumbers={false}
                        monacoOptions={MONACO_READONLY_CONFIG}
                      />
                    </div>
                    <Button
                      variant={'secondary'}
                      icon="edit"
                      size={'md'}
                      onClick={() => handleEditRoutingTemplate(channelFilter, channelFilterId)}
                    />
                  </HorizontalGroup>

                  <div className={cx('routing-alert')}>
                    <Alert
                      severity="info"
                      title={
                        (
                          <Text type="primary">
                            If the Routing template evaluates to True, the alert will be grouped with the Grouping
                            template and proceed to the following steps
                          </Text>
                        ) as any
                      }
                    />
                  </div>
                </VerticalGroup>
              )}
            </div>
          ),
        },
        IntegrationHelper.hasChatopsInstalled(store) && {
          isHidden: false,
          isCollapsible: false,
          isTextIcon: true,
          collapsedView: null,
          canHoverIcon: false,
          expandedView: () => (
            <div className={cx('adjust-element-padding')}>
              <VerticalGroup spacing="sm">
                <Text customTag="h6" type="primary">
                  Publish to ChatOps
                </Text>
                <ChatOpsConnectors channelFilterId={channelFilterId} showLineNumber={false} />
              </VerticalGroup>
            </div>
          ),
        },
        {
          isHidden: false,
          isCollapsible: false,
          isExpanded: false,
          isTextIcon: true,
          collapsedView: null,
          canHoverIcon: false,
          expandedView: () => (
            <div className={cx('adjust-element-padding')}>
              <VerticalGroup spacing="sm">
                <Text customTag="h6" type="primary">
                  Trigger escalation chain
                </Text>

                <div data-testid="escalation-chain-select">
                  <HorizontalGroup spacing={'xs'}>
                    <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
                      <Select
                        isClearable
                        isSearchable
                        width={'auto'}
                        menuShouldPortal
                        className={cx('select', 'control')}
                        placeholder="Select escalation chain"
                        isLoading={isRefreshingEscalationChains}
                        onChange={onEscalationChainChange}
                        options={Object.keys(escalationChainStore.items).map(
                          (eschalationChainId: EscalationChain['id']) => ({
                            id: escalationChainStore.items[eschalationChainId].id,
                            value: escalationChainStore.items[eschalationChainId].name,
                            label: escalationChainStore.items[eschalationChainId].name,
                          })
                        )}
                        value={escChainDisplayName}
                        getOptionLabel={(item: SelectableValue) => {
                          return (
                            <>
                              <Text>{item.label} </Text>
                              <TeamName
                                team={grafanaTeamStore.items[escalationChainStore.items[item.id].team]}
                                size="small"
                              />
                            </>
                          );
                        }}
                      ></Select>
                    </WithPermissionControlTooltip>

                    <Tooltip placement={'top'} content={'Reload list'}>
                      <Button variant={'secondary'} icon={'sync'} size={'md'} onClick={onEscalationChainsRefresh} />
                    </Tooltip>

                    <PluginLink className={cx('hover-button')} target="_blank" query={escalationChainRedirectObj}>
                      <Tooltip
                        placement={'top'}
                        content={channelFilter.escalation_chain ? 'Edit escalation chain' : 'Add an escalation chain'}
                      >
                        <Button variant={'secondary'} icon={'external-link-alt'} size={'md'} />
                      </Tooltip>
                    </PluginLink>

                    {channelFilter.escalation_chain && (
                      <Button
                        variant={'secondary'}
                        onClick={() => setState({ isEscalationCollapsed: !isEscalationCollapsed })}
                      >
                        <HorizontalGroup>
                          <Text type="link">{isEscalationCollapsed ? 'Show' : 'Hide'} escalation chain</Text>
                          {isEscalationCollapsed && <Icon name={'angle-right'} />}
                          {!isEscalationCollapsed && <Icon name={'angle-up'} />}
                        </HorizontalGroup>
                      </Button>
                    )}
                  </HorizontalGroup>
                </div>
                {!isEscalationCollapsed && (
                  <ReadOnlyEscalationChain escalationChainId={channelFilter.escalation_chain} />
                )}
              </VerticalGroup>
            </div>
          ),
        },
      ];

      return configs;
    };

    return (
      <>
        <IntegrationBlock
          noContent={false}
          key={channelFilterId}
          heading={
            <HorizontalGroup justify={'space-between'}>
              <HorizontalGroup spacing={'md'}>
                <TooltipBadge
                  borderType="success"
                  text={CommonIntegrationHelper.getRouteConditionWording(channelFilterIds, routeIndex)}
                  tooltipTitle={CommonIntegrationHelper.getRouteConditionTooltipWording(channelFilterIds, routeIndex)}
                  tooltipContent={undefined}
                  className={cx('u-margin-right-xs')}
                />
              </HorizontalGroup>
              <HorizontalGroup spacing={'xs'}>
                <RouteButtonsDisplay
                  alertReceiveChannelId={alertReceiveChannelId}
                  channelFilterId={channelFilterId}
                  routeIndex={routeIndex}
                  onItemMove={onItemMove}
                  setRouteIdForDeletion={() => setState({ routeIdForDeletion: channelFilterId })}
                  openRouteTemplateEditor={() => handleEditRoutingTemplate(channelFilter, channelFilterId)}
                />
              </HorizontalGroup>
            </HorizontalGroup>
          }
          content={
            <IntegrationCollapsibleTreeView
              configElements={getTreeViewElements() as any}
              isRouteView
              startingElemPosition="0%"
            />
          }
        />
        {routeIdForDeletion && (
          <ConfirmModal
            isOpen
            title="Delete route?"
            body="Are you sure you want to delete this route?"
            confirmText="Delete"
            icon="exclamation-triangle"
            onConfirm={onRouteDeleteConfirm}
            onDismiss={() => setState({ routeIdForDeletion: undefined })}
          />
        )}
      </>
    );

    async function onRouteDeleteConfirm() {
      setState({ routeIdForDeletion: undefined });
      onRouteDelete(routeIdForDeletion);
    }

    async function onEscalationChainChange(value: { id: string }) {
      const newEscalationChainId = value ? value.id : null;
      await alertReceiveChannelStore.saveChannelFilter(channelFilterId, {
        escalation_chain: newEscalationChainId,
      });
      escalationChainStore.updateItems(); // to update number_of_integrations and number_of_routes
      escalationPolicyStore.updateEscalationPolicies(newEscalationChainId);
    }

    async function onEscalationChainsRefresh() {
      setState({ isRefreshingEscalationChains: true });
      await escalationChainStore.updateItems();
      setState({ isRefreshingEscalationChains: false });
    }

    function handleEditRoutingTemplate(channelFilter, channelFilterId) {
      if (channelFilter.filtering_term_type === 0) {
        onEditRegexpTemplate(channelFilterId);
      } else {
        openEditTemplateModal('route_template', channelFilterId);
      }
    }
  }
);

const ReadOnlyEscalationChain: React.FC<{ escalationChainId: string }> = ({ escalationChainId }) => {
  return <EscalationChainSteps isDisabled id={escalationChainId} />;
};

interface RouteButtonsDisplayProps {
  alertReceiveChannelId: ApiSchemas['AlertReceiveChannel']['id'];
  channelFilterId: ChannelFilter['id'];
  routeIndex: number;
  setRouteIdForDeletion(): void;
  openRouteTemplateEditor(): void;
  onItemMove();
}

export const RouteButtonsDisplay: React.FC<RouteButtonsDisplayProps> = ({
  alertReceiveChannelId,
  channelFilterId,
  routeIndex,
  setRouteIdForDeletion,
  openRouteTemplateEditor,
  onItemMove,
}) => {
  const { alertReceiveChannelStore } = useStore();
  const channelFilter = alertReceiveChannelStore.channelFilters[channelFilterId];
  const channelFilterIds = alertReceiveChannelStore.channelFilterIds[alertReceiveChannelId];

  return (
    <HorizontalGroup spacing={'xs'}>
      {routeIndex > 0 && !channelFilter.is_default && (
        <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
          <Tooltip placement="top" content={'Move Up'}>
            <Button variant={'secondary'} onClick={onRouteMoveUp} icon={'arrow-up'} size={'sm'} />
          </Tooltip>
        </WithPermissionControlTooltip>
      )}

      {routeIndex < channelFilterIds.length - 2 && !channelFilter.is_default && (
        <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
          <Tooltip placement="top" content={'Move Down'}>
            <Button variant={'secondary'} onClick={onRouteMoveDown} icon={'arrow-down'} size={'sm'} />
          </Tooltip>
        </WithPermissionControlTooltip>
      )}

      {!channelFilter.is_default && (
        <WithContextMenu
          renderMenuItems={() => (
            <div className={cx('integrations-actionsList')}>
              <div className={cx('integrations-actionItem')} onClick={openRouteTemplateEditor}>
                <Text type="primary">Edit Template</Text>
              </div>

              <CopyToClipboard text={channelFilter.id} onCopy={() => openNotification('Route ID is copied')}>
                <div className={cx('integrations-actionItem')}>
                  <HorizontalGroup spacing={'xs'}>
                    <Icon name="copy" />

                    <Text type="primary">UID: {channelFilter.id}</Text>
                  </HorizontalGroup>
                </div>
              </CopyToClipboard>

              <div className={cx('thin-line-break')} />

              <WithPermissionControlTooltip key="delete" userAction={UserActions.IntegrationsWrite}>
                <div className={cx('integrations-actionItem')} onClick={onDelete}>
                  <Text type="danger">
                    <HorizontalGroup spacing={'xs'}>
                      <Icon name="trash-alt" />
                      <span>Delete Route</span>
                    </HorizontalGroup>
                  </Text>
                </div>
              </WithPermissionControlTooltip>
            </div>
          )}
        >
          {({ openMenu }) => (
            <HamburgerMenuIcon
              openMenu={openMenu}
              listBorder={2}
              listWidth={200}
              className={'hamburgerMenu--small'}
              stopPropagation={true}
            />
          )}
        </WithContextMenu>
      )}
    </HorizontalGroup>
  );

  function onDelete() {
    setRouteIdForDeletion();
  }

  function onRouteMoveDown(e: React.SyntheticEvent) {
    e.stopPropagation();
    alertReceiveChannelStore.moveChannelFilterToPosition(alertReceiveChannelId, routeIndex, routeIndex + 1);
    onItemMove();
  }

  function onRouteMoveUp(e: React.SyntheticEvent) {
    e.stopPropagation();
    alertReceiveChannelStore.moveChannelFilterToPosition(alertReceiveChannelId, routeIndex, routeIndex - 1);
    onItemMove();
  }
};
