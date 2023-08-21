import React, { ChangeEvent } from 'react';

import { SelectableValue } from '@grafana/data';
import { Button, Input, Select, IconButton } from '@grafana/ui';
import cn from 'classnames/bind';
import moment from 'moment-timezone';
import { SortableElement } from 'react-sortable-hoc';
import reactStringReplace from 'react-string-replace';

import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import TimeRange from 'components/TimeRange/TimeRange';
import Timeline from 'components/Timeline/Timeline';
import GSelect from 'containers/GSelect/GSelect';
import TeamName from 'containers/TeamName/TeamName';
import UserTooltip from 'containers/UserTooltip/UserTooltip';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { prepareEscalationPolicy } from 'models/escalation_policy/escalation_policy.helpers';
import {
  EscalationPolicy as EscalationPolicyType,
  EscalationPolicyOption,
} from 'models/escalation_policy/escalation_policy.types';
import { GrafanaTeamStore } from 'models/grafana_team/grafana_team';
import { OutgoingWebhookStore } from 'models/outgoing_webhook/outgoing_webhook';
import { ScheduleStore } from 'models/schedule/schedule';
import { WaitDelay } from 'models/wait_delay';
import { SelectOption } from 'state/types';
import { getVar } from 'utils/DOM';
import { UserActions } from 'utils/authorization';

import DragHandle from './DragHandle';
import PolicyNote from './PolicyNote';

import styles from './EscalationPolicy.module.css';

const cx = cn.bind(styles);

interface ElementSortableProps {
  index: number;
}

export interface EscalationPolicyProps extends ElementSortableProps {
  data: EscalationPolicyType;
  waitDelays?: any[];
  isDisabled?: boolean;
  numMinutesInWindowOptions: SelectOption[];
  channels?: any[];
  onChange: (id: EscalationPolicyType['id'], value: Partial<EscalationPolicyType>) => void;
  onDelete: (data: EscalationPolicyType) => void;
  escalationChoices: any[];
  number: number;
  backgroundColor: string;
  isSlackInstalled: boolean;
  teamStore: GrafanaTeamStore;
  outgoingWebhookStore: OutgoingWebhookStore;
  scheduleStore: ScheduleStore;
}

export class EscalationPolicy extends React.Component<EscalationPolicyProps, any> {
  render() {
    const { data, escalationChoices, number, backgroundColor, isDisabled } = this.props;
    const { id, step, is_final } = data;

    const escalationOption = escalationChoices.find(
      (escalationOption: EscalationPolicyOption) => escalationOption.value === step
    );

    return (
      <Timeline.Item
        key={id}
        contentClassName={cx('root')}
        number={number}
        textColor={isDisabled ? getVar('--tag-text-success') : undefined}
        backgroundColor={backgroundColor}
      >
        <WithPermissionControlTooltip disableByPaywall userAction={UserActions.EscalationChainsWrite}>
          <DragHandle />
        </WithPermissionControlTooltip>
        {escalationOption &&
          reactStringReplace(escalationOption.display_name, /\{\{([^}]+)\}\}/g, this.replacePlaceholder)}
        {this._renderNote()}
        {is_final || isDisabled ? null : (
          <WithPermissionControlTooltip className={cx('delete')} userAction={UserActions.EscalationChainsWrite}>
            <IconButton
              name="trash-alt"
              className={cx('delete', 'control')}
              onClick={this._handleDelete}
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
        return this._renderNotifyToUsersQueue();
      case 'wait_delay':
        return this._renderWaitDelays();
      case 'slack_user_group':
        return this._renderNotifyUserGroup();
      case 'schedule':
        return this._renderNotifySchedule();
      case 'custom_webhook':
        return this._renderTriggerCustomWebhook();
      case 'num_alerts_in_window':
        return this.renderNumAlertsInWindow();
      case 'num_minutes_in_window':
        return this.renderNumMinutesInWindowOptions();
      default:
        console.warn('Unknown escalation step placeholder');
        return '';
    }
  };

  _renderNote() {
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

  private _renderNotifyToUsersQueue() {
    const { data, isDisabled } = this.props;
    const { notify_to_users_queue } = data;

    return (
      <WithPermissionControlTooltip
        key="users-multiple"
        disableByPaywall
        userAction={UserActions.EscalationChainsWrite}
      >
        <GSelect
          isMulti
          showSearch
          allowClear
          disabled={isDisabled}
          modelName="userStore"
          displayField="username"
          valueField="pk"
          placeholder="Select Users"
          className={cx('select', 'control', 'multiSelect')}
          value={notify_to_users_queue}
          onChange={this._getOnChangeHandler('notify_to_users_queue')}
          getOptionLabel={({ value }: SelectableValue) => <UserTooltip id={value} />}
          width={'auto'}
        />
      </WithPermissionControlTooltip>
    );
  }

  private renderImportance() {
    const { data, isDisabled } = this.props;
    const { important } = data;

    return (
      <WithPermissionControlTooltip key="importance" disableByPaywall userAction={UserActions.EscalationChainsWrite}>
        <Select
          menuShouldPortal
          className={cx('select', 'control')}
          disabled={isDisabled}
          value={Number(important)}
          // @ts-ignore
          onChange={this._getOnSelectChangeHandler('important')}
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

  private renderTimeRange() {
    const { data, isDisabled } = this.props;

    return (
      <WithPermissionControlTooltip key="time-range" disableByPaywall userAction={UserActions.EscalationChainsWrite}>
        <TimeRange
          from={data.from_time}
          to={data.to_time}
          disabled={isDisabled}
          onChange={this._getOnTimeRangeChangeHandler()}
          className={cx('select', 'control')}
        />
      </WithPermissionControlTooltip>
    );
  }

  private _renderWaitDelays() {
    const { data, isDisabled, waitDelays = [] } = this.props;
    const { wait_delay } = data;

    return (
      <WithPermissionControlTooltip key="wait-delay" disableByPaywall userAction={UserActions.EscalationChainsWrite}>
        <Select
          menuShouldPortal
          disabled={isDisabled}
          placeholder="Select Wait Delay"
          className={cx('select', 'control')}
          // @ts-ignore
          value={wait_delay}
          onChange={this._getOnSelectChangeHandler('wait_delay')}
          options={waitDelays.map((waitDelay: WaitDelay) => ({
            value: waitDelay.value,
            label: waitDelay.display_name,
          }))}
          width={'auto'}
        />
      </WithPermissionControlTooltip>
    );
  }

  private renderNumAlertsInWindow() {
    const { data, isDisabled } = this.props;
    const { num_alerts_in_window } = data;

    return (
      <WithPermissionControlTooltip
        key="num_alerts_in_window"
        disableByPaywall
        userAction={UserActions.EscalationChainsWrite}
      >
        <Input
          placeholder="Count"
          disabled={isDisabled}
          className={cx('control')}
          value={num_alerts_in_window}
          onChange={this._getOnInputChangeHandler('num_alerts_in_window')}
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

  private renderNumMinutesInWindowOptions() {
    const { data, isDisabled, numMinutesInWindowOptions = [] } = this.props;
    const { num_minutes_in_window } = data;

    return (
      <WithPermissionControlTooltip
        key="num_minutes_in_window"
        disableByPaywall
        userAction={UserActions.EscalationChainsWrite}
      >
        <Select
          menuShouldPortal
          disabled={isDisabled}
          placeholder="Period"
          className={cx('select', 'control')}
          // @ts-ignore
          value={num_minutes_in_window}
          onChange={this._getOnSelectChangeHandler('num_minutes_in_window')}
          options={numMinutesInWindowOptions.map((waitDelay: SelectOption) => ({
            value: waitDelay.value,
            label: waitDelay.display_name,
          }))}
        />
      </WithPermissionControlTooltip>
    );
  }

  private _renderNotifySchedule() {
    const { data, isDisabled, teamStore, scheduleStore } = this.props;
    const { notify_schedule } = data;

    return (
      <WithPermissionControlTooltip
        key="notify_schedule"
        disableByPaywall
        userAction={UserActions.EscalationChainsWrite}
      >
        <GSelect
          showSearch
          allowClear
          disabled={isDisabled}
          modelName="scheduleStore"
          displayField="name"
          valueField="id"
          placeholder="Select Schedule"
          className={cx('select', 'control')}
          value={notify_schedule}
          onChange={this._getOnChangeHandler('notify_schedule')}
          getOptionLabel={(item: SelectableValue) => {
            const team = teamStore.items[scheduleStore.items[item.value].team];
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

  private _renderNotifyUserGroup() {
    const { data, isDisabled } = this.props;
    const { notify_to_group } = data;

    return (
      <WithPermissionControlTooltip
        key="notify_to_group"
        disableByPaywall
        userAction={UserActions.EscalationChainsWrite}
      >
        <GSelect
          disabled={isDisabled}
          modelName="userGroupStore"
          displayField="name"
          valueField="id"
          placeholder="Select User Group"
          className={cx('select', 'control')}
          value={notify_to_group}
          onChange={this._getOnChangeHandler('notify_to_group')}
          width={'auto'}
        />
      </WithPermissionControlTooltip>
    );
  }

  private _renderTriggerCustomWebhook() {
    const { data, isDisabled, teamStore, outgoingWebhookStore } = this.props;
    const { custom_webhook } = data;

    return (
      <WithPermissionControlTooltip
        key="custom-webhook"
        disableByPaywall
        userAction={UserActions.EscalationChainsWrite}
      >
        <GSelect
          showSearch
          disabled={isDisabled}
          modelName="outgoingWebhookStore"
          displayField="name"
          valueField="id"
          placeholder="Select Webhook"
          className={cx('select', 'control')}
          value={custom_webhook}
          onChange={this._getOnChangeHandler('custom_webhook')}
          getOptionLabel={(item: SelectableValue) => {
            const team = teamStore.items[outgoingWebhookStore.items[item.value].team];
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

  _getOnSelectChangeHandler = (field: string) => {
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

  _getOnInputChangeHandler = (field: string) => {
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

  _getOnChangeHandler = (field: string) => {
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

  _getOnTimeRangeChangeHandler() {
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

  _handleDelete = () => {
    const { onDelete, data } = this.props;

    onDelete(data);
  };
}

export default SortableElement(EscalationPolicy) as React.ComponentClass<EscalationPolicyProps>;
