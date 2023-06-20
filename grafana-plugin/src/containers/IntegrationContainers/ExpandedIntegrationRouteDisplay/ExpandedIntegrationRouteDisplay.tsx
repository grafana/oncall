import React, { useEffect, useReducer, useState } from 'react';

import { SelectableValue } from '@grafana/data';
import {
  Button,
  HorizontalGroup,
  InlineLabel,
  VerticalGroup,
  Icon,
  Tooltip,
  ConfirmModal,
  LoadingPlaceholder,
} from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import CopyToClipboard from 'react-copy-to-clipboard';

import HamburgerMenu from 'components/HamburgerMenu/HamburgerMenu';
import IntegrationBlock from 'components/Integrations/IntegrationBlock';
import IntegrationBlockItem from 'components/Integrations/IntegrationBlockItem';
import MonacoEditor from 'components/MonacoEditor/MonacoEditor';
import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import TooltipBadge from 'components/TooltipBadge/TooltipBadge';
import { WithContextMenu } from 'components/WithContextMenu/WithContextMenu';
import { ChatOpsConnectors } from 'containers/AlertRules/parts';
import EscalationChainSteps from 'containers/EscalationChainSteps/EscalationChainSteps';
import GSelect from 'containers/GSelect/GSelect';
import styles from 'containers/IntegrationContainers/ExpandedIntegrationRouteDisplay/ExpandedIntegrationRouteDisplay.module.scss';
import TeamName from 'containers/TeamName/TeamName';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { AlertTemplatesDTO } from 'models/alert_templates';
import { ChannelFilter } from 'models/channel_filter/channel_filter.types';
import CommonIntegrationHelper from 'pages/integration_2/CommonIntegration2.helper';
import { MONACO_INPUT_HEIGHT_SMALL, MONACO_OPTIONS } from 'pages/integration_2/Integration2.config';
import IntegrationHelper from 'pages/integration_2/Integration2.helper';
import { useStore } from 'state/useStore';
import { openNotification } from 'utils';
import { UserActions } from 'utils/authorization';

const cx = cn.bind(styles);

const ACTIONS_LIST_WIDTH = 200;
const ACTIONS_LIST_BORDER = 2;

interface ExpandedIntegrationRouteDisplayProps {
  alertReceiveChannelId: AlertReceiveChannel['id'];
  channelFilterId: ChannelFilter['id'];
  routeIndex: number;
  templates: AlertTemplatesDTO[];
  openEditTemplateModal: (templateName: string | string[], channelFilterId?: ChannelFilter['id']) => void;
  onEditRegexpTemplate: (channelFilterId: ChannelFilter['id']) => void;
}

interface ExpandedIntegrationRouteDisplayState {
  isEscalationCollapsed: boolean;
  isRefreshingEscalationChains: boolean;
  routeIdForDeletion: string;
}

const ExpandedIntegrationRouteDisplay: React.FC<ExpandedIntegrationRouteDisplayProps> = observer(
  ({ alertReceiveChannelId, channelFilterId, templates, routeIndex, openEditTemplateModal, onEditRegexpTemplate }) => {
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
      Promise.all([escalationChainStore.updateItems(), telegramChannelStore.updateItems()]).then(() =>
        setIsLoading(false)
      );
    }, []);

    const channelFilter = alertReceiveChannelStore.channelFilters[channelFilterId];
    const channelFiltersTotal = Object.keys(alertReceiveChannelStore.channelFilters);
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

    return (
      <>
        <IntegrationBlock
          hasCollapsedBorder
          key={channelFilterId}
          heading={
            <HorizontalGroup justify={'space-between'}>
              <HorizontalGroup spacing={'md'}>
                <TooltipBadge
                  borderType="success"
                  text={CommonIntegrationHelper.getRouteConditionWording(channelFilterIds, routeIndex)}
                  tooltipTitle={CommonIntegrationHelper.getRouteConditionTooltipWording(channelFilterIds, routeIndex)}
                  tooltipContent={undefined}
                />
              </HorizontalGroup>
              <HorizontalGroup spacing={'xs'}>
                <RouteButtonsDisplay
                  alertReceiveChannelId={alertReceiveChannelId}
                  channelFilterId={channelFilterId}
                  routeIndex={routeIndex}
                  setRouteIdForDeletion={() => setState({ routeIdForDeletion: channelFilterId })}
                />
              </HorizontalGroup>
            </HorizontalGroup>
          }
          content={
            <VerticalGroup spacing="xs">
              {routeIndex !== channelFiltersTotal.length - 1 && (
                <IntegrationBlockItem>
                  <VerticalGroup>
                    <Text type="secondary">
                      If the Routing Template is True, group alerts with the Grouping Template, send them to messengers,
                      and trigger the escalation chain.
                    </Text>
                  </VerticalGroup>
                </IntegrationBlockItem>
              )}
              {/* Show Routing Template only for If/Else Routes, not for Default */}
              {!isDefault && (
                <IntegrationBlockItem>
                  <HorizontalGroup spacing="xs">
                    <InlineLabel
                      width={20}
                      tooltip="Routing Template should be True for the alert to go to this route."
                    >
                      Routing Template
                    </InlineLabel>
                    <div className={cx('input', 'input--short')}>
                      <MonacoEditor
                        value={channelFilterTemplate}
                        disabled={true}
                        height={MONACO_INPUT_HEIGHT_SMALL}
                        data={templates}
                        showLineNumbers={false}
                        monacoOptions={MONACO_OPTIONS}
                      />
                    </div>
                    <Button
                      variant={'secondary'}
                      icon="edit"
                      size={'md'}
                      onClick={() => handleEditRoutingTemplate(channelFilter, channelFilterId)}
                    />
                  </HorizontalGroup>
                </IntegrationBlockItem>
              )}

              {IntegrationHelper.hasChatopsInstalled(store) && (
                <IntegrationBlockItem>
                  <VerticalGroup spacing="md">
                    <Text type="primary">Publish to ChatOps</Text>
                    <ChatOpsConnectors channelFilterId={channelFilterId} showLineNumber={false} />
                  </VerticalGroup>
                </IntegrationBlockItem>
              )}

              <IntegrationBlockItem>
                <VerticalGroup>
                  <HorizontalGroup spacing={'xs'}>
                    <InlineLabel
                      width={20}
                      tooltip="The escalation chain determines who and when to notify when an alert group starts."
                    >
                      Escalation chain
                    </InlineLabel>
                    <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
                      <GSelect
                        showSearch
                        width={'auto'}
                        modelName="escalationChainStore"
                        className={cx('select', 'control')}
                        placeholder="Select escalation chain"
                        isLoading={isRefreshingEscalationChains}
                        displayField="name"
                        onChange={onEscalationChainChange}
                        value={channelFilter.escalation_chain}
                        getOptionLabel={(item: SelectableValue) => {
                          return (
                            <>
                              <Text>{item.label} </Text>
                              <TeamName
                                team={grafanaTeamStore.items[escalationChainStore.items[item.value].team]}
                                size="small"
                              />
                            </>
                          );
                        }}
                      />
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

                  {isEscalationCollapsed && (
                    <ReadOnlyEscalationChain escalationChainId={channelFilter.escalation_chain} />
                  )}
                </VerticalGroup>
              </IntegrationBlockItem>
            </VerticalGroup>
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
      await alertReceiveChannelStore.deleteChannelFilter(routeIdForDeletion);
      openNotification('Route has been deleted');
    }

    function onEscalationChainChange(value) {
      alertReceiveChannelStore
        .saveChannelFilter(channelFilterId, {
          escalation_chain: value,
        })
        .then(() => {
          escalationChainStore.updateItems(); // to update number_of_integrations and number_of_routes
          escalationPolicyStore.updateEscalationPolicies(value);
        });
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
  alertReceiveChannelId: AlertReceiveChannel['id'];
  channelFilterId: ChannelFilter['id'];
  routeIndex: number;
  setRouteIdForDeletion(): void;
}

export const RouteButtonsDisplay: React.FC<RouteButtonsDisplayProps> = ({
  alertReceiveChannelId,
  channelFilterId,
  routeIndex,
  setRouteIdForDeletion,
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
              <CopyToClipboard text={channelFilter.id} onCopy={() => openNotification('Route ID is copied')}>
                <div className={cx('integrations-actionItem')}>
                  <HorizontalGroup spacing={'xs'}>
                    <Icon name="copy" />

                    <Text type="primary">UID: {channelFilter.id}</Text>
                  </HorizontalGroup>
                </div>
              </CopyToClipboard>

              <div className="thin-line-break" />

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
            <HamburgerMenu
              openMenu={openMenu}
              listBorder={ACTIONS_LIST_BORDER}
              listWidth={ACTIONS_LIST_WIDTH}
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
  }

  function onRouteMoveUp(e: React.SyntheticEvent) {
    e.stopPropagation();
    alertReceiveChannelStore.moveChannelFilterToPosition(alertReceiveChannelId, routeIndex, routeIndex - 1);
  }
};

export default ExpandedIntegrationRouteDisplay;
