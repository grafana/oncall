import React, { ChangeEvent } from 'react';

import { cx } from '@emotion/css';
import { GrafanaTheme2, SelectableValue } from '@grafana/data';
import { Button, Input, Select, IconButton, withTheme2, Themeable2 } from '@grafana/ui';
import { observer } from 'mobx-react';
import moment from 'moment-timezone';
import { SortableElement } from 'react-sortable-hoc';
import reactStringReplace from 'react-string-replace';
import { getLabelBackgroundTextColorObject } from 'styles/utils.styles';

import { PluginLink } from 'components/PluginLink/PluginLink';
import { Text } from 'components/Text/Text';
import { TimeRange } from 'components/TimeRange/TimeRange';
import { Timeline } from 'components/Timeline/Timeline';
import { GSelect } from 'containers/GSelect/GSelect';
import { TeamName } from 'containers/TeamName/TeamName';
import { UserTooltip } from 'containers/UserTooltip/UserTooltip';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { prepareEscalationPolicy } from 'models/escalation_policy/escalation_policy.helpers';
import {
  EscalationPolicy as EscalationPolicyType,
  EscalationPolicyOption,
} from 'models/escalation_policy/escalation_policy.types';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
import { Schedule } from 'models/schedule/schedule.types';
import { UserHelper } from 'models/user/user.helpers';
import { UserGroup } from 'models/user_group/user_group.types';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { SelectOption, WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import { UserActions } from 'utils/authorization/authorization';

import { DragHandle } from './DragHandle';
import { getEscalationPolicyStyles } from './EscalationPolicy.styles';
import { PolicyNote } from './PolicyNote';

interface ElementSortableProps extends WithStoreProps {
  index: number;
}

export interface EscalationPolicyProps extends ElementSortableProps, Themeable2 {
  data: EscalationPolicyType;
  waitDelays?: any[];
  isDisabled?: boolean;
  numMinutesInWindowOptions: SelectOption[];
  channels?: any[];
  onChange: (id: EscalationPolicyType['id'], value: Partial<EscalationPolicyType>) => void;
  onDelete: (data: EscalationPolicyType) => void;
  escalationChoices: any[];
  number: number;
  backgroundClassName?: string;
  backgroundHexNumber?: string;
  isSlackInstalled: boolean;
  theme: GrafanaTheme2;
}

@observer
class _EscalationPolicy extends React.Component<EscalationPolicyProps, any> {
  private styles: ReturnType<typeof getEscalationPolicyStyles>;

  constructor(props: EscalationPolicyProps) {
    super(props);
    this.styles = getEscalationPolicyStyles(props.theme);
  }

  componentDidUpdate(prevProps: Readonly<EscalationPolicyProps>): void {
    if (prevProps.theme !== this.props.theme) {
      // fetch new styles whenever the theme changes
      this.styles = getEscalationPolicyStyles(this.props.theme);
      this.forceUpdate();
    }
  }

  render() {
    const { data, escalationChoices, number, isDisabled, backgroundClassName, backgroundHexNumber } = this.props;
    const { id, step, is_final } = data;

    const escalationOption = escalationChoices.find(
      (escalationOption: EscalationPolicyOption) => escalationOption.value === step
    );

    const { textColor: itemTextColor } = getLabelBackgroundTextColorObject('green', this.props.theme);

    return (
      <Timeline.Item
        key={id}
        contentClassName={cx(this.styles.root)}
        number={number}
        textColor={isDisabled ? itemTextColor : undefined}
        backgroundClassName={backgroundClassName}
        backgroundHexNumber={backgroundHexNumber}
      >
        {!isDisabled && (
          <WithPermissionControlTooltip userAction={UserActions.EscalationChainsWrite}>
            <DragHandle />
          </WithPermissionControlTooltip>
        )}
        {escalationOption &&
          reactStringReplace(escalationOption.display_name, /\{\{([^}]+)\}\}/g, this.replacePlaceholder)}
        {this.renderNote()}
        {is_final || isDisabled ? null : (
          <WithPermissionControlTooltip
            className={cx(this.styles.delete)}
            userAction={UserActions.EscalationChainsWrite}
          >
            <IconButton
              name="trash-alt"
              className={cx(this.styles.delete, this.styles.control)}
              onClick={this.handleDelete}
              size="sm"
              tooltip="Delete"
              tooltipPlacement="top"
            />
          </WithPermissionControlTooltip>
        )}
      </Timeline.Item>
    );
  }

  replacePlaceholder = (match: string) => {
    switch (match) {
      case 'importance':
        return this.renderImportance();
      case 'timerange':
        return this.renderTimeRange();
      case 'users':
        return this.renderNotifyToUsersQueue();
      case 'wait_delay':
        return this.renderWaitDelays();
      case 'slack_user_group':
        return this.renderNotifyUserGroup();
      case 'team':
        return this.renderNotifyTeam();
      case 'schedule':
        return this.renderNotifySchedule();
      case 'custom_webhook':
        return this.renderTriggerCustomWebhook();
      case 'num_alerts_in_window':
        return this.renderNumAlertsInWindow();
      case 'num_minutes_in_window':
        return this.renderNumMinutesInWindowOptions();
      default:
        console.warn('Unknown escalation step placeholder');
        return '';
    }
  };

  renderNote() {
    const { data, isSlackInstalled, escalationChoices } = this.props;
    const { step } = data;

    const option = escalationChoices.find((option) => option.value === step);

    if (!isSlackInstalled && option?.slack_integration_required) {
      return (
        <PolicyNote type="danger">
          Slack Integration required{' '}
          <PluginLink query={{ page: 'chat-ops' }}>
            <Button size="sm" fill="text">
              Install
            </Button>
          </PluginLink>
        </PolicyNote>
      );
    }

    switch (step) {
      case 13:
        return <PolicyNote>{`Your timezone is ${moment.tz.guess()}`}</PolicyNote>;

      default:
        return null;
    }
  }

  renderNotifyToUsersQueue() {
    const {
      data,
      isDisabled,
      store: { userStore },
    } = this.props;
    const { notify_to_users_queue } = data;

    return (
      <WithPermissionControlTooltip key="users-multiple" userAction={UserActions.EscalationChainsWrite}>
        <GSelect<ApiSchemas['User']>
          isMulti
          showSearch
          allowClear
          disabled={isDisabled}
          displayField="username"
          valueField="pk"
          placeholder="Select Users"
          className={cx(this.styles.select, this.styles.control, this.styles.multiSelect)}
          value={notify_to_users_queue}
          onChange={this.getOnChangeHandler('notify_to_users_queue')}
          getOptionLabel={({ value }: SelectableValue) => <UserTooltip id={value} />}
          width={'auto'}
          items={userStore.items}
          fetchItemsFn={userStore.fetchItems}
          fetchItemFn={async (id) => await userStore.fetchItemById({ userPk: id, skipIfAlreadyPending: true })}
          getSearchResult={() => UserHelper.getSearchResult(userStore)}
        />
      </WithPermissionControlTooltip>
    );
  }

  renderImportance() {
    const { data, isDisabled } = this.props;
    const { important } = data;

    return (
      <WithPermissionControlTooltip key="importance" userAction={UserActions.EscalationChainsWrite}>
        <Select
          menuShouldPortal
          className={cx(this.styles.select, this.styles.control)}
          disabled={isDisabled}
          value={Number(important)}
          // @ts-ignore
          onChange={this.getOnSelectChangeHandler('important')}
          options={[
            {
              value: 0,
              label: 'Default',
              // @ts-ignore
              description: (
                <>
                  Manage&nbsp;"Default&nbsp;notifications"
                  <br />
                  in personal settings
                </>
              ),
            },
            {
              value: 1,
              label: 'Important',
              // @ts-ignore
              description: (
                <>
                  Manage&nbsp;"Important&nbsp;notifications"
                  <br />
                  in personal settings
                </>
              ),
            },
          ]}
          width={'auto'}
        />
      </WithPermissionControlTooltip>
    );
  }

  renderTimeRange() {
    const { data, isDisabled } = this.props;

    return (
      <WithPermissionControlTooltip key="time-range" userAction={UserActions.EscalationChainsWrite}>
        <TimeRange
          from={data.from_time}
          to={data.to_time}
          disabled={isDisabled}
          onChange={this.getOnTimeRangeChangeHandler()}
          className={cx(this.styles.select, this.styles.control)}
        />
      </WithPermissionControlTooltip>
    );
  }

  renderWaitDelays() {
    const { data, isDisabled, waitDelays = [] } = this.props;
    const { wait_delay } = data;

    return (
      <WithPermissionControlTooltip key="wait-delay" userAction={UserActions.EscalationChainsWrite}>
        <Select
          menuShouldPortal
          disabled={isDisabled}
          placeholder="Select Wait Delay"
          className={cx(this.styles.select, this.styles.control)}
          // @ts-ignore
          value={wait_delay}
          onChange={this.getOnSelectChangeHandler('wait_delay')}
          options={waitDelays.map((waitDelay: SelectOption) => ({
            value: waitDelay.value,
            label: waitDelay.display_name,
          }))}
          width={'auto'}
        />
      </WithPermissionControlTooltip>
    );
  }

  renderNumAlertsInWindow() {
    const { data, isDisabled } = this.props;
    const { num_alerts_in_window } = data;

    return (
      <WithPermissionControlTooltip key="num_alerts_in_window" userAction={UserActions.EscalationChainsWrite}>
        <Input
          placeholder="Count"
          disabled={isDisabled}
          className={cx(this.styles.control)}
          value={num_alerts_in_window}
          onChange={this.getOnInputChangeHandler('num_alerts_in_window')}
          ref={(node) => {
            if (node) {
              node.setAttribute('type', 'number');
              node.setAttribute('min', '1');
            }
          }}
        />
      </WithPermissionControlTooltip>
    );
  }

  renderNumMinutesInWindowOptions() {
    const { data, isDisabled, numMinutesInWindowOptions = [] } = this.props;
    const { num_minutes_in_window } = data;

    return (
      <WithPermissionControlTooltip key="num_minutes_in_window" userAction={UserActions.EscalationChainsWrite}>
        <Select
          menuShouldPortal
          disabled={isDisabled}
          placeholder="Period"
          className={cx(this.styles.select, this.styles.control)}
          // @ts-ignore
          value={num_minutes_in_window}
          onChange={this.getOnSelectChangeHandler('num_minutes_in_window')}
          options={numMinutesInWindowOptions.map((waitDelay: SelectOption) => ({
            value: waitDelay.value,
            label: waitDelay.display_name,
          }))}
        />
      </WithPermissionControlTooltip>
    );
  }

  renderNotifySchedule() {
    const {
      data,
      isDisabled,
      store: { grafanaTeamStore, scheduleStore },
    } = this.props;
    const { notify_schedule } = data;

    return (
      <WithPermissionControlTooltip key="notify_schedule" userAction={UserActions.EscalationChainsWrite}>
        <GSelect<Schedule>
          showSearch
          allowClear
          disabled={isDisabled}
          items={scheduleStore.items}
          fetchItemsFn={scheduleStore.updateItems}
          fetchItemFn={scheduleStore.updateItem}
          getSearchResult={scheduleStore.getSearchResult}
          displayField="name"
          valueField="id"
          placeholder="Select Schedule"
          className={cx(this.styles.select, this.styles.control)}
          value={notify_schedule}
          onChange={this.getOnChangeHandler('notify_schedule')}
          getOptionLabel={(item: SelectableValue) => {
            const team = grafanaTeamStore.items[scheduleStore.items[item.value].team];
            return (
              <>
                <Text>{item.label} </Text>
                <TeamName team={team} size="small" />
              </>
            );
          }}
        />
      </WithPermissionControlTooltip>
    );
  }

  renderNotifyUserGroup() {
    const {
      data,
      isDisabled,
      store: { userGroupStore },
    } = this.props;
    const { notify_to_group } = data;

    return (
      <WithPermissionControlTooltip key="notify_to_group" userAction={UserActions.EscalationChainsWrite}>
        <GSelect<UserGroup[]>
          disabled={isDisabled}
          items={userGroupStore.items}
          fetchItemsFn={userGroupStore.updateItems}
          fetchItemFn={() => undefined}
          // TODO: fetchItemFn
          getSearchResult={userGroupStore.getSearchResult}
          displayField="name"
          valueField="id"
          placeholder="Select User Group"
          className={cx(this.styles.select, this.styles.control)}
          value={notify_to_group}
          onChange={this.getOnChangeHandler('notify_to_group')}
          width={'auto'}
        />
      </WithPermissionControlTooltip>
    );
  }

  renderTriggerCustomWebhook() {
    const {
      data,
      isDisabled,
      store: { grafanaTeamStore, outgoingWebhookStore },
    } = this.props;
    const { custom_webhook } = data;

    return (
      <WithPermissionControlTooltip key="custom-webhook" userAction={UserActions.EscalationChainsWrite}>
        <GSelect<ApiSchemas['Webhook']>
          showSearch
          disabled={isDisabled}
          items={outgoingWebhookStore.items}
          fetchItemsFn={outgoingWebhookStore.updateItems}
          fetchItemFn={outgoingWebhookStore.updateItem}
          getSearchResult={outgoingWebhookStore.getSearchResult}
          displayField="name"
          valueField="id"
          placeholder="Select Webhook"
          className={cx(this.styles.select, this.styles.control)}
          value={custom_webhook}
          onChange={this.getOnChangeHandler('custom_webhook')}
          getOptionLabel={(item: SelectableValue) => {
            const team = grafanaTeamStore.items[outgoingWebhookStore.items[item.value].team];
            return (
              <>
                <Text>{item.label} </Text>
                <TeamName team={team} size="small" />
              </>
            );
          }}
          width={'auto'}
          filterOptions={(id) => {
            const webhook = outgoingWebhookStore.items[id];
            return webhook.trigger_type_name === 'Escalation step';
          }}
        />
      </WithPermissionControlTooltip>
    );
  }

  renderNotifyTeam() {
    const {
      data,
      isDisabled,
      store: { grafanaTeamStore },
    } = this.props;
    const { notify_to_team_members } = data;

    return (
      <WithPermissionControlTooltip key="notify_to_team_members" userAction={UserActions.EscalationChainsWrite}>
        <GSelect<GrafanaTeam>
          disabled={isDisabled}
          items={grafanaTeamStore.items}
          fetchItemsFn={grafanaTeamStore.updateItems}
          fetchItemFn={grafanaTeamStore.fetchItemById}
          getSearchResult={grafanaTeamStore.getSearchResult}
          displayField="name"
          valueField="id"
          placeholder="Select Team"
          className={cx('select', 'control')}
          value={notify_to_team_members}
          onChange={this.getOnChangeHandler('notify_to_team_members')}
          width={'auto'}
        />
      </WithPermissionControlTooltip>
    );
  }

  getOnSelectChangeHandler = (field: string) => {
    return (option: SelectableValue) => {
      const { data, onChange = () => {} } = this.props;
      const { id } = data;

      const newData: Partial<EscalationPolicyType> = {
        ...prepareEscalationPolicy(data),
        [field]: option.value,
      };

      onChange(id, newData);
    };
  };

  getOnInputChangeHandler = (field: string) => {
    const { data, onChange = () => {} } = this.props;
    const { id } = data;

    return (e: ChangeEvent<HTMLInputElement>) => {
      const newData: Partial<EscalationPolicyType> = {
        ...prepareEscalationPolicy(data),
        [field]: e.currentTarget.value,
      };

      onChange(id, newData);
    };
  };

  getOnChangeHandler = (field: string) => {
    return (value: any) => {
      const { data, onChange = () => {} } = this.props;
      const { id } = data;

      const newData: Partial<EscalationPolicyType> = {
        ...prepareEscalationPolicy(data),
        [field]: value,
      };

      onChange(id, newData);
    };
  };

  getOnTimeRangeChangeHandler() {
    return (value: string[]) => {
      const { data, onChange = () => {} } = this.props;
      const { id } = data;

      const newData: Partial<EscalationPolicyType> = {
        ...prepareEscalationPolicy(data),
        from_time: value[0],
        to_time: value[1],
      };

      onChange(id, newData);
    };
  }

  handleDelete = () => {
    const { onDelete, data } = this.props;

    onDelete(data);
  };
}

export const EscalationPolicy = withMobXProviderContext(
  SortableElement(withTheme2(_EscalationPolicy)) as React.ComponentClass<EscalationPolicyProps>
);
