import React, { ChangeEvent } from 'react';

import { cx } from '@emotion/css';
import { SelectableValue } from '@grafana/data';
import { Button, Input, Select, IconButton, withTheme2, Themeable2 } from '@grafana/ui';
import { isNumber } from 'lodash-es';
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
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import { UserActions } from 'utils/authorization/authorization';
import { openWarningNotification } from 'utils/utils';

import { DragHandle } from './DragHandle';
import { getEscalationPolicyStyles } from './EscalationPolicy.styles';
import { POLICY_DURATION_LIST_MINUTES } from './Policy.consts';
import { PolicyNote } from './PolicyNote';

interface ElementSortableProps extends WithStoreProps {
  index: number;
}

interface EscalationPolicyBaseProps {
  data: EscalationPolicyType;
  isDisabled?: boolean;
  channels?: any[];
  onChange: (id: EscalationPolicyType['id'], value: Partial<EscalationPolicyType>) => void;
  onDelete: (data: EscalationPolicyType) => void;
  escalationChoices: any[];
  number: number;
  backgroundClassName?: string;
  backgroundHexNumber?: string;
  isSlackInstalled: boolean;
}

// We export the base props class, the actual definition is wrapped by MobX
// MobX adds extra props that we do not need to pass on the consuming side
export interface EscalationPolicyProps extends EscalationPolicyBaseProps, ElementSortableProps, Themeable2 {}

@observer
class _EscalationPolicy extends React.Component<EscalationPolicyProps, any> {
  private styles: ReturnType<typeof getEscalationPolicyStyles>;

  render() {
    const { data, escalationChoices, number, isDisabled, backgroundClassName, backgroundHexNumber, theme } = this.props;
    const { id, step, is_final } = data;

    const escalationOption = escalationChoices.find(
      (escalationOption: EscalationPolicyOption) => escalationOption.value === step
    );

    const { textColor: itemTextColor } = getLabelBackgroundTextColorObject('green', theme);
    const styles = getEscalationPolicyStyles(theme);

    return (
      <Timeline.Item
        key={id}
        contentClassName={styles.root}
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
          <WithPermissionControlTooltip className={styles.delete} userAction={UserActions.EscalationChainsWrite}>
            <IconButton
              name="trash-alt"
              className={cx(styles.delete, styles.control)}
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
      theme,
      store: { userStore },
    } = this.props;
    const { notify_to_users_queue } = data;
    const styles = getEscalationPolicyStyles(theme);

    return (
      <WithPermissionControlTooltip key="users-multiple" userAction={UserActions.EscalationChainsWrite}>
        <GSelect<ApiSchemas['User']>
          isMulti
          allowClear
          disabled={isDisabled}
          displayField="username"
          valueField="pk"
          placeholder="Select Users"
          className={cx(styles.select, styles.control, styles.multiSelect)}
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
    const { data, isDisabled, theme } = this.props;
    const { important } = data;
    const styles = getEscalationPolicyStyles(theme);

    return (
      <WithPermissionControlTooltip key="importance" userAction={UserActions.EscalationChainsWrite}>
        <Select
          menuShouldPortal
          className={cx(styles.select, styles.control)}
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
    const { data, isDisabled, theme } = this.props;
    const styles = getEscalationPolicyStyles(theme);

    return (
      <WithPermissionControlTooltip key="time-range" userAction={UserActions.EscalationChainsWrite}>
        <TimeRange
          from={data.from_time}
          to={data.to_time}
          disabled={isDisabled}
          onChange={this.getOnTimeRangeChangeHandler()}
          className={cx(styles.select, styles.control)}
        />
      </WithPermissionControlTooltip>
    );
  }

  renderWaitDelays() {
    const { data, isDisabled, theme } = this.props;
    const { wait_delay } = data;

    const styles = getEscalationPolicyStyles(theme);
    const silenceOptions: SelectableValue[] = [...POLICY_DURATION_LIST_MINUTES];

    const waitDelayInSeconds = wait_delay ? parseFloat(wait_delay) : 0;
    const waitDelayInMinutes = waitDelayInSeconds / 60;

    const waitDelayOptionItem = silenceOptions.find((opt) => opt.value === waitDelayInMinutes) || {
      value: waitDelayInMinutes,
      label: waitDelayInMinutes,
    }; // either find it in the list or initialize it to show in the dropdown

    return (
      <WithPermissionControlTooltip key="wait-delay" userAction={UserActions.EscalationChainsWrite}>
        <Select
          menuShouldPortal
          disabled={isDisabled}
          placeholder="Select Wait Delay"
          className={cx(styles.select, styles.control)}
          value={waitDelayInSeconds ? waitDelayOptionItem : undefined}
          onChange={(option: SelectableValue) =>
            this.getOnSelectChangeHandler('wait_delay')({ value: option.value * 60 })
          }
          options={silenceOptions}
          width={'auto'}
          allowCustomValue
          onCreateOption={(option) => this.onCreateOption('wait_delay', option, true)}
        />
      </WithPermissionControlTooltip>
    );
  }

  renderNumAlertsInWindow() {
    const { data, isDisabled, theme } = this.props;
    const { num_alerts_in_window } = data;
    const styles = getEscalationPolicyStyles(theme);

    return (
      <WithPermissionControlTooltip key="num_alerts_in_window" userAction={UserActions.EscalationChainsWrite}>
        <Input
          placeholder="Count"
          disabled={isDisabled}
          className={styles.control}
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
    const { data, isDisabled, theme } = this.props;
    const { num_minutes_in_window } = data;
    const styles = getEscalationPolicyStyles(theme);

    const options: SelectableValue[] = [...POLICY_DURATION_LIST_MINUTES];

    const optionValue = options.find((opt) => opt.value === num_minutes_in_window) || {
      value: num_minutes_in_window,
      label: num_minutes_in_window,
    }; // either find it in the list or initialize it to show in the dropdown

    return (
      <WithPermissionControlTooltip key="num_minutes_in_window" userAction={UserActions.EscalationChainsWrite}>
        <Select
          menuShouldPortal
          disabled={isDisabled}
          placeholder="Period"
          className={cx(styles.select, styles.control)}
          value={num_minutes_in_window ? optionValue : undefined}
          onChange={this.getOnSelectChangeHandler('num_minutes_in_window')}
          allowCustomValue
          onCreateOption={(option) => this.onCreateOption('num_minutes_in_window', option)}
          options={options}
        />
      </WithPermissionControlTooltip>
    );
  }

  renderNotifySchedule() {
    const {
      data,
      theme,
      isDisabled,
      store: { grafanaTeamStore, scheduleStore },
    } = this.props;
    const { notify_schedule } = data;
    const styles = getEscalationPolicyStyles(theme);

    return (
      <WithPermissionControlTooltip key="notify_schedule" userAction={UserActions.EscalationChainsWrite}>
        <GSelect<Schedule>
          allowClear
          disabled={isDisabled}
          items={scheduleStore.items}
          fetchItemsFn={scheduleStore.updateItems}
          fetchItemFn={scheduleStore.updateItem}
          getSearchResult={scheduleStore.getSearchResult}
          displayField="name"
          valueField="id"
          placeholder="Select Schedule"
          className={cx(styles.select, styles.control)}
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
      theme,
      isDisabled,
      store: { userGroupStore },
    } = this.props;

    const { notify_to_group } = data;
    const styles = getEscalationPolicyStyles(theme);

    return (
      <WithPermissionControlTooltip key="notify_to_group" userAction={UserActions.EscalationChainsWrite}>
        <GSelect<UserGroup>
          allowClear
          disabled={isDisabled}
          items={userGroupStore.items}
          fetchItemsFn={userGroupStore.updateItems}
          fetchItemFn={userGroupStore.fetchItemById}
          getSearchResult={userGroupStore.getSearchResult}
          displayField="name"
          valueField="id"
          placeholder="Select User Group"
          className={cx(styles.select, styles.control)}
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
      theme,
      isDisabled,
      store: { grafanaTeamStore, outgoingWebhookStore },
    } = this.props;

    const { custom_webhook } = data;
    const styles = getEscalationPolicyStyles(theme);

    return (
      <WithPermissionControlTooltip key="custom-webhook" userAction={UserActions.EscalationChainsWrite}>
        <GSelect<ApiSchemas['Webhook']>
          disabled={isDisabled}
          items={outgoingWebhookStore.items}
          fetchItemsFn={outgoingWebhookStore.updateItems}
          fetchItemFn={outgoingWebhookStore.updateItem}
          getSearchResult={outgoingWebhookStore.getSearchResult}
          displayField="name"
          valueField="id"
          placeholder="Select Webhook"
          className={cx(styles.select, styles.control)}
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

  onCreateOption = (fieldName: string, option: string, parseToSeconds = false) => {
    if (!isNumber(+option)) {
      return;
    }

    const num = parseFloat(option);

    if (!Number.isInteger(+option)) {
      return openWarningNotification('Given number must be an integer');
    }

    if (num < 1 || num > 24 * 60) {
      return openWarningNotification('Given number must be in the range of 1 minute and 24 hours');
    }

    this.getOnSelectChangeHandler(fieldName)({ value: num * (parseToSeconds ? 60 : 1) });
  };

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
  SortableElement(withTheme2(_EscalationPolicy))
) as unknown as React.ComponentClass<EscalationPolicyBaseProps>;
