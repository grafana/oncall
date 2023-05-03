import React, { useReducer } from 'react';

import { SelectableValue } from '@grafana/data';
import { Button, HorizontalGroup, InlineLabel, VerticalGroup, Icon, Tooltip, ConfirmModal } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import MonacoJinja2Editor from 'components/MonacoJinja2Editor/MonacoJinja2Editor';
import PluginLink from 'components/PluginLink/PluginLink';
import Tag from 'components/Tag/Tag';
import Text from 'components/Text/Text';
import { ChatOpsConnectors } from 'containers/AlertRules/parts';
import EscalationChainSteps from 'containers/EscalationChainSteps/EscalationChainSteps';
import GSelect from 'containers/GSelect/GSelect';
import TeamName from 'containers/TeamName/TeamName';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { AlertReceiveChannel } from 'models/alert_receive_channel';
import { AlertTemplatesDTO } from 'models/alert_templates';
import { ChannelFilter } from 'models/channel_filter/channel_filter.types';
import { useStore } from 'state/useStore';
import { getVar } from 'utils/DOM';
import { UserActions } from 'utils/authorization';

import styles from './ExpandedIntegrationRouteDisplay.module.scss';
import { MONACO_INPUT_HEIGHT_SMALL, MONACO_OPTIONS } from './Integration2.config';
import IntegrationHelper from './Integration2.helper';
import IntegrationBlock from './IntegrationBlock';
import IntegrationBlockItem from './IntegrationBlockItem';

const cx = cn.bind(styles);

interface ExpandedIntegrationRouteDisplayProps {
  alertReceiveChannelId: AlertReceiveChannel['id'];
  channelFilterId: ChannelFilter['id'];
  routeIndex: number;
  templates: AlertTemplatesDTO[];
  openEditTemplateModal: (templateName: string | string[]) => void;
}

interface ExpandedIntegrationRouteDisplayState {
  isEscalationCollapsed: boolean;
  isRefreshingEscalationChains: boolean;
  routeIdForDeletion: string;
}

const ExpandedIntegrationRouteDisplay: React.FC<ExpandedIntegrationRouteDisplayProps> = observer(
  ({ alertReceiveChannelId, channelFilterId, templates, routeIndex, openEditTemplateModal }) => {
    const { escalationPolicyStore, escalationChainStore, alertReceiveChannelStore, grafanaTeamStore } = useStore();
    const hasChatOpsConnectors = false;

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

    const channelFilter = alertReceiveChannelStore.channelFilters[channelFilterId];
    const channelFiltersTotal = Object.keys(alertReceiveChannelStore.channelFilters);
    if (!channelFilter) {
      return null;
    }

    return (
      <>
        <IntegrationBlock
          hasCollapsedBorder
          heading={
            <HorizontalGroup justify={'space-between'}>
              <HorizontalGroup spacing={'md'}>
                <Tag color={getVar('--tag-primary')}>
                  {IntegrationHelper.getRouteConditionWording(alertReceiveChannelStore.channelFilters, routeIndex)}
                </Tag>
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
                  <HorizontalGroup spacing="xs">
                    <InlineLabel width={20} tooltip={'TODO: Add text'}>
                      Routing Template
                    </InlineLabel>
                    <div className={cx('input', 'input--short')}>
                      <MonacoJinja2Editor
                        value={IntegrationHelper.getFilteredTemplate(channelFilter.filtering_term, false)}
                        disabled={true}
                        height={MONACO_INPUT_HEIGHT_SMALL}
                        data={templates}
                        showLineNumbers={false}
                        monacoOptions={MONACO_OPTIONS}
                      />
                    </div>
                    <Button variant={'secondary'} icon="edit" size={'md'} onClick={undefined} />
                    <Button variant="secondary" size="md" onClick={() => openEditTemplateModal('routing')}>
                      <Text type="link">Help</Text>
                      <Icon name="angle-down" size="sm" />
                    </Button>
                  </HorizontalGroup>
                </IntegrationBlockItem>
              )}

              {routeIndex !== channelFiltersTotal.length - 1 && (
                <IntegrationBlockItem>
                  <VerticalGroup>
                    <Text type="secondary">
                      If the Routing template evaluates to True, the alert will be grouped with the Grouping template
                      and proceed to the following steps
                    </Text>
                  </VerticalGroup>
                </IntegrationBlockItem>
              )}

              {hasChatOpsConnectors && (
                <IntegrationBlockItem>
                  <VerticalGroup spacing="md">
                    <Text type="primary">Publish to ChatOps</Text>
                    <ChatOpsConnectors channelFilterId={channelFilterId} />
                  </VerticalGroup>
                </IntegrationBlockItem>
              )}

              <IntegrationBlockItem>
                <VerticalGroup>
                  <HorizontalGroup spacing={'xs'}>
                    <InlineLabel width={20}>Escalation chain</InlineLabel>
                    <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
                      <GSelect
                        showSearch
                        modelName="escalationChainStore"
                        isLoading={isRefreshingEscalationChains}
                        displayField="name"
                        placeholder="Select Escalation Chain"
                        className={cx('select', 'control')}
                        value={channelFilter.escalation_chain}
                        onChange={onEscalationChainChange}
                        showWarningIfEmptyValue={true}
                        width={'auto'}
                        icon={'list-ul'}
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

                    <Button variant={'secondary'} icon={'sync'} size={'md'} onClick={onEscalationChainsRefresh} />
                    <PluginLink
                      className={cx('hover-button')}
                      target="_blank"
                      query={{ page: 'escalations', id: channelFilter.escalation_chain }}
                    >
                      <Button variant={'secondary'} icon={'external-link-alt'} size={'md'} />
                    </PluginLink>
                    <Button
                      variant={'secondary'}
                      onClick={() => setState({ isEscalationCollapsed: !isEscalationCollapsed })}
                    >
                      <HorizontalGroup>
                        <Text type="link">Show escalation chain</Text>
                        {isEscalationCollapsed && <Icon name={'angle-right'} />}
                        {!isEscalationCollapsed && <Icon name={'angle-up'} />}
                      </HorizontalGroup>
                    </Button>
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
    }

    function onEscalationChainChange(value: string) {
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
  const channelFiltersTotal = Object.keys(alertReceiveChannelStore.channelFilters);

  return (
    <HorizontalGroup>
      {routeIndex > 0 && !channelFilter.is_default && (
        <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
          <Tooltip placement="top" content={'Move Up'}>
            <Button variant={'secondary'} onClick={onRouteMoveUp} icon={'arrow-up'} size={'xs'} />
          </Tooltip>
        </WithPermissionControlTooltip>
      )}

      {routeIndex < channelFiltersTotal.length - 2 && !channelFilter.is_default && (
        <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
          <Tooltip placement="top" content={'Move Down'}>
            <Button variant={'secondary'} onClick={onRouteMoveDown} icon={'arrow-down'} size={'xs'} />
          </Tooltip>
        </WithPermissionControlTooltip>
      )}

      {!channelFilter.is_default && (
        <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
          <Tooltip placement="top" content={'Delete'}>
            <Button variant={'secondary'} icon={'trash-alt'} size={'xs'} onClick={setRouteIdForDeletion} />
          </Tooltip>
        </WithPermissionControlTooltip>
      )}
    </HorizontalGroup>
  );

  function onRouteMoveDown() {
    alertReceiveChannelStore.moveChannelFilterToPosition(alertReceiveChannelId, routeIndex, routeIndex + 1);
  }

  function onRouteMoveUp() {
    alertReceiveChannelStore.moveChannelFilterToPosition(alertReceiveChannelId, routeIndex, routeIndex - 1);
  }
};

export default ExpandedIntegrationRouteDisplay;
