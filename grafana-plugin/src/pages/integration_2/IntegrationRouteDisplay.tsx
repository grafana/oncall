import React, { useReducer } from 'react';
import GSelect from 'containers/GSelect/GSelect';
import { SelectableValue } from '@grafana/data';
import { ChannelFilter } from 'models/channel_filter/channel_filter.types';
import IntegrationBlock from './IntegrationBlock';
import { Button, HorizontalGroup, InlineLabel, VerticalGroup, Icon, Tooltip } from '@grafana/ui';
import Tag from 'components/Tag/Tag';
import { getVar } from 'utils/DOM';
import Text from 'components/Text/Text';
import IntegrationBlockItem from './IntegrationBlockItem';

import styles from './IntegrationRouteDisplay.module.scss';
import cn from 'classnames/bind';
import MonacoJinja2Editor from 'components/MonacoJinja2Editor/MonacoJinja2Editor';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { UserActions } from 'utils/authorization';
import TeamName from 'containers/TeamName/TeamName';
import { MONACO_INPUT_HEIGHT_SMALL, MONACO_OPTIONS } from './Integration2.config';
import { AlertTemplatesDTO } from 'models/alert_templates';
import { useStore } from 'state/useStore';
import EscalationChainSteps from 'containers/EscalationChainSteps/EscalationChainSteps';
import { observer } from 'mobx-react';
import { ChatOpsConnectors } from 'containers/AlertRules/parts';
import IntegrationHelper from './Integration2.helper';
import PluginLink from 'components/PluginLink/PluginLink';

const cx = cn.bind(styles);

interface IntegrationRouteDisplayProps {
  channelFilterId: ChannelFilter['id'];
  routeIndex: number;
  templates: AlertTemplatesDTO[];
}

interface IntegrationRouteDisplayState {
  isEscalationCollapsed: boolean;
  isRefreshingEscalationChains: boolean;
}

const IntegrationRouteDisplay: React.FC<IntegrationRouteDisplayProps> = observer(
  ({ channelFilterId, templates, routeIndex }) => {
    const { escalationPolicyStore, escalationChainStore, alertReceiveChannelStore, grafanaTeamStore } = useStore();
    const hasChatOpsConnectors = false;

    const [{ isEscalationCollapsed, isRefreshingEscalationChains }, setState] = useReducer(
      (state: IntegrationRouteDisplayState, newState: Partial<IntegrationRouteDisplayState>) => ({
        ...state,
        ...newState,
      }),
      {
        isEscalationCollapsed: true,
        isRefreshingEscalationChains: false,
      }
    );

    const channelFilter = alertReceiveChannelStore.channelFilters[channelFilterId];
    const channelFiltersTotal = Object.keys(alertReceiveChannelStore.channelFilters);
    if (!channelFilter) return null;

    return (
      <IntegrationBlock
        heading={
          <HorizontalGroup justify={'space-between'}>
            <HorizontalGroup spacing={'md'}>
              <Tag color={getVar('--tag-primary')}>{getConditionWording(routeIndex)}</Tag>
              {channelFilter.filtering_term && <Text type="secondary">{channelFilter.filtering_term}</Text>}
            </HorizontalGroup>
            <HorizontalGroup spacing={'xs'}>
              {routeIndex > 0 && !channelFilter.is_default && (
                <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
                  <Tooltip placement="top" content={'Move Up'}>
                    <Button variant={'secondary'} onClick={onRouteMoveUp} icon={'arrow-up'} size={'md'} />
                  </Tooltip>
                </WithPermissionControlTooltip>
              )}

              {routeIndex < channelFiltersTotal.length - 2 && !channelFilter.is_default && (
                <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
                  <Tooltip placement="top" content={'Move Down'}>
                    <Button variant={'secondary'} onClick={onRouteMoveDown} icon={'arrow-down'} size={'md'} />
                  </Tooltip>
                </WithPermissionControlTooltip>
              )}

              {!channelFilter.is_default && (
                <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
                  <Tooltip placement="top" content={'Delete'}>
                    <Button variant={'secondary'} icon={'trash-alt'} size={'md'} onClick={onRouteDelete} />
                  </Tooltip>
                </WithPermissionControlTooltip>
              )}
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
                  <Button variant="secondary" size="md" onClick={undefined}>
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
                    If the Routing template evaluates to True, the alert will be grouped with the Grouping template and
                    proceed to the following steps
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
    );

    function onRouteMoveDown(event: React.SyntheticEvent) {
      event.stopPropagation();
      // alertReceiveChannelStore.moveChannelFilterToPosition(alertReceiveChannelId, index, index - 1);
    }

    function onRouteMoveUp(event: React.SyntheticEvent) {
      event.stopPropagation();
      // alertReceiveChannelStore.moveChannelFilterToPosition(alertReceiveChannelId, index, index + 1);
    }

    function onRouteDelete(event: React.SyntheticEvent) {
      event.stopPropagation();
    }

    function getConditionWording(routeIndex) {
      const totalCount = Object.keys(alertReceiveChannelStore.channelFilters).length;
      if (routeIndex === totalCount - 1) return 'Default';
      return routeIndex ? 'Else' : 'If';
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

export default IntegrationRouteDisplay;
