import React, { useReducer, useState } from 'react';
import GSelect from 'containers/GSelect/GSelect';
import { PRIVATE_CHANNEL_NAME } from 'models/slack_channel/slack_channel.config';
import { SelectableValue } from '@grafana/data';
import { ChannelFilter } from 'models/channel_filter/channel_filter.types';
import IntegrationBlock from './IntegrationBlock';
import { Button, HorizontalGroup, InlineLabel, VerticalGroup, Switch, Icon } from '@grafana/ui';
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

const cx = cn.bind(styles);

interface IntegrationRouteDisplayProps {
  channelFilter: ChannelFilter;
  routeIndex: number;
  templates: AlertTemplatesDTO[];
}

interface IntegrationRouteDisplayState {
  isEscalationCollapsed: boolean;
  isRefreshingEscalationChains: boolean;
  selectedEscalationChain: string;
}

const IntegrationRouteDisplay: React.FC<IntegrationRouteDisplayProps> = ({ channelFilter, templates, routeIndex }) => {
  const { teamStore, escalationChainStore, grafanaTeamStore } = useStore();
  const [{ isEscalationCollapsed, isRefreshingEscalationChains, selectedEscalationChain }, setState] = useReducer(
    (state: IntegrationRouteDisplayState, newState: Partial<IntegrationRouteDisplayState>) => ({
      ...state,
      ...newState,
    }),
    {
      isEscalationCollapsed: true,
      isRefreshingEscalationChains: false,
      selectedEscalationChain: channelFilter.escalation_chain,
    }
  );

  return (
    <IntegrationBlock
      heading={
        <HorizontalGroup justify={'space-between'}>
          <HorizontalGroup spacing={'md'}>
            <Tag color={getVar('--tag-primary')}>{routeIndex ? 'ELSE IF' : 'IF'}</Tag>
            {channelFilter.filtering_term && <Text type="secondary">{channelFilter.filtering_term}</Text>}
          </HorizontalGroup>
          <HorizontalGroup spacing={'xs'}>
            <Button variant={'secondary'} icon={'arrow-up'} size={'md'} onClick={undefined} />
            <Button variant={'secondary'} icon={'arrow-down'} size={'md'} onClick={undefined} />
            <Button variant={'secondary'} icon={'trash-alt'} size={'md'} onClick={undefined} />
          </HorizontalGroup>
        </HorizontalGroup>
      }
      content={
        <VerticalGroup spacing="xs">
          <IntegrationBlockItem>
            <HorizontalGroup spacing="xs">
              <InlineLabel width={20} tooltip={'TODO: Add text'}>
                Routing Template
              </InlineLabel>
              <div className={cx('input', 'input--short')}>
                <MonacoJinja2Editor
                  value={channelFilter.filtering_term}
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

          <IntegrationBlockItem>
            <VerticalGroup>
              <Text type="secondary">
                If the Routing template evaluates to True, the alert will be grouped with the Grouping template and
                proceed to the following steps
              </Text>
            </VerticalGroup>
          </IntegrationBlockItem>

          <IntegrationBlockItem>
            <VerticalGroup spacing="md">
              <Text type="primary">Publish to ChatOps</Text>
              <HorizontalGroup spacing="md">
                <Switch value={undefined} onChange={(_event) => {}} />
                <InlineLabel width={20}>Slack channel</InlineLabel>
                <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
                  <GSelect
                    showSearch
                    allowClear
                    className={cx('select', 'control')}
                    modelName="slackChannelStore"
                    displayField="display_name"
                    valueField="id"
                    placeholder="Select Slack Channel"
                    value={channelFilter.slack_channel?.id || teamStore.currentTeam?.slack_channel?.id}
                    onChange={handleSlackChannelChange}
                    nullItemName={PRIVATE_CHANNEL_NAME}
                  />
                </WithPermissionControlTooltip>
              </HorizontalGroup>
            </VerticalGroup>
          </IntegrationBlockItem>

          <IntegrationBlockItem>
            <VerticalGroup>
              <HorizontalGroup>
                <InlineLabel width={20}>Escalation chain</InlineLabel>
                <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
                  <GSelect
                    showSearch
                    modelName="escalationChainStore"
                    isLoading={isRefreshingEscalationChains}
                    displayField="name"
                    placeholder="Select Escalation Chain"
                    className={cx('select', 'control')}
                    value={selectedEscalationChain}
                    onChange={(value) => setState({ selectedEscalationChain: value })}
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
                <Button variant={'secondary'} icon={'edit'} size={'md'} onClick={openEscalationChainInNewWindow} />
                <Button
                  variant={'secondary'}
                  onClick={() => setState({ isEscalationCollapsed: !isEscalationCollapsed })}
                >
                  <HorizontalGroup>
                    <Text type="link">Show escalation chain</Text>
                    {isEscalationCollapsed && <Icon name={'angle-down'} />}
                    {!isEscalationCollapsed && <Icon name={'angle-up'} />}
                  </HorizontalGroup>
                </Button>
              </HorizontalGroup>

              {isEscalationCollapsed && <ReadOnlyEscalationChain escalationChainId={selectedEscalationChain} />}
            </VerticalGroup>
          </IntegrationBlockItem>
        </VerticalGroup>
      }
    />
  );

  async function onEscalationChainsRefresh() {
    setState({ isRefreshingEscalationChains: true });
    await escalationChainStore.updateItems();
    setState({ isRefreshingEscalationChains: false });
  }

  function handleSlackChannelChange() {}

  // TODO: Change it to point to actual location
  function openEscalationChainInNewWindow() {
    window.open('http://google.ro', '_blank');
  }
};

const ReadOnlyEscalationChain: React.FC<{ escalationChainId: ChannelFilter['id'] }> = ({ escalationChainId }) => {
  return <EscalationChainSteps isDisabled id={escalationChainId} />;
};

export default IntegrationRouteDisplay;
