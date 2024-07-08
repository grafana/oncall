import React from 'react';

import { css, cx } from '@emotion/css';
import { GrafanaTheme2, SelectableValue } from '@grafana/data';
import { Button, IconButton, Select, Themeable2, withTheme2 } from '@grafana/ui';
import { isNumber } from 'lodash';
import { SortableElement } from 'react-sortable-hoc';

import { PluginLink } from 'components/PluginLink/PluginLink';
import { Timeline } from 'components/Timeline/Timeline';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { Channel } from 'models/channel/channel';
import { NotificationPolicyType, prepareNotificationPolicy } from 'models/notification_policy/notification_policy';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { AppFeature } from 'state/features';
import { RootStore } from 'state/rootStore';
import { SelectOption } from 'state/types';
import { UserAction } from 'utils/authorization/authorization';
import { openWarningNotification } from 'utils/utils';

import { DragHandle } from './DragHandle';
import { POLICY_DURATION_LIST_MINUTES, POLICY_DURATION_LIST_SECONDS } from './Policy.consts';
import { PolicyNote } from './PolicyNote';

export interface NotificationPolicyProps extends Themeable2 {
  data: NotificationPolicyType;
  slackTeamIdentity?: {
    general_log_channel_pk: Channel['id'];
  };
  slackUserIdentity?: ApiSchemas['User']['slack_user_identity'];
  onChange: (id: NotificationPolicyType['id'], value: NotificationPolicyType) => void;
  onDelete: (id: string) => void;
  notificationChoices: any[];
  channels?: any[];
  waitDelays?: SelectOption[];
  notifyByOptions?: SelectOption[];
  telegramVerified: boolean;
  phoneStatus: number;
  isMobileAppConnected: boolean;
  showCloudConnectionWarning: boolean;
  color: string;
  number: number;
  userAction: UserAction;
  store: RootStore;
  isDisabled: boolean;
}

export class NotificationPolicy extends React.Component<NotificationPolicyProps, any> {
  private styles: ReturnType<typeof getStyles>;

  constructor(props: NotificationPolicyProps) {
    super(props);
    this.styles = getStyles(this.props.theme);
  }

  componentDidUpdate(prevProps: Readonly<NotificationPolicyProps>): void {
    if (prevProps.theme !== this.props.theme) {
      // fetch new styles whenever the theme changes
      this.styles = getStyles(this.props.theme);
      this.forceUpdate();
    }
  }

  render() {
    const { data, notificationChoices, number, color, userAction, isDisabled } = this.props;
    const { id, step } = data;

    return (
      <Timeline.Item className={cx(this.styles.root)} number={number} backgroundHexNumber={color}>
        <div className={cx(this.styles.step)}>
          {!isDisabled && (
            <WithPermissionControlTooltip userAction={userAction}>
              <DragHandle />
            </WithPermissionControlTooltip>
          )}
          <WithPermissionControlTooltip userAction={userAction}>
            <Select
              className={cx(this.styles.select, this.styles.control)}
              onChange={this._getOnChangeHandler('step')}
              value={step}
              options={notificationChoices.map((option: any) => ({ label: option.display_name, value: option.value }))}
              disabled={isDisabled}
            />
          </WithPermissionControlTooltip>
          {this._renderControls(isDisabled)}
          <WithPermissionControlTooltip userAction={userAction}>
            <IconButton
              aria-label="Remove"
              className={cx(this.styles.control)}
              name="trash-alt"
              onClick={this._getDeleteClickHandler(id)}
              variant="secondary"
              disabled={isDisabled}
            />
          </WithPermissionControlTooltip>
          {this._renderNote()}
        </div>
      </Timeline.Item>
    );
  }

  _renderControls(disabled: boolean) {
    const { data } = this.props;
    const { step } = data;

    switch (step) {
      case 0:
        return <>{this._renderWaitDelays(disabled)}</>;

      case 1:
        return <>{this._renderNotifyBy(disabled)}</>;

      default:
        return null;
    }
  }

  _renderSlackNote() {
    const { slackTeamIdentity, slackUserIdentity } = this.props;

    if (!slackTeamIdentity) {
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

    if (!slackUserIdentity) {
      return <PolicyNote type="danger">Slack account is not connected</PolicyNote>;
    }

    return null;
  }

  _renderPhoneNote() {
    const { phoneStatus } = this.props;

    switch (phoneStatus) {
      case 0:
        return <PolicyNote type="danger">Cloud is not synced</PolicyNote>;
      case 1:
        return <PolicyNote type="danger">User is not matched with cloud</PolicyNote>;
      case 2:
        return <PolicyNote type="danger">Phone number is not verified</PolicyNote>;
      case 3:
        return <PolicyNote type="success">Phone number is verified</PolicyNote>;

      default:
        return null;
    }
  }

  _renderMobileAppNote() {
    const { isMobileAppConnected, showCloudConnectionWarning } = this.props;

    if (showCloudConnectionWarning) {
      return <PolicyNote type="danger">Cloud is not connected</PolicyNote>;
    }

    if (!isMobileAppConnected) {
      return <PolicyNote type="danger">Mobile app is not connected</PolicyNote>;
    }

    return <PolicyNote type="success">Mobile app is connected</PolicyNote>;
  }

  _renderTelegramNote() {
    const { telegramVerified, store } = this.props;

    if (!store.hasFeature(AppFeature.Telegram)) {
      return null;
    }

    return telegramVerified ? (
      <PolicyNote type="success">Telegram is connected</PolicyNote>
    ) : (
      <PolicyNote type="danger">Telegram is not connected</PolicyNote>
    );
  }

  private _renderWaitDelays(disabled: boolean) {
    const { data, userAction } = this.props;
    const { wait_delay } = data;

    const optionsList = [...POLICY_DURATION_LIST_MINUTES];

    const waitDelayInSeconds = parseFloat(wait_delay);
    const waitDelayInMinutes = waitDelayInSeconds / 60;

    const optionValue = POLICY_DURATION_LIST_SECONDS.find((delay) => delay.duration === waitDelayInMinutes) || {
      value: waitDelayInMinutes,
      label: waitDelayInMinutes,
    };

    return (
      <WithPermissionControlTooltip userAction={userAction}>
        <div className={this.styles.container}>
          <Select
            key="wait-delay"
            placeholder="Wait Delay"
            className={cx(this.styles.delay, this.styles.control)}
            value={wait_delay ? optionValue : undefined}
            disabled={disabled}
            onChange={(option: SelectableValue) => this._getOnChangeHandler('wait_delay')({ value: option.value * 60 })}
            options={optionsList}
            allowCustomValue
            onCreateOption={(option: string) => {
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

              this._getOnChangeHandler('wait_delay')({ value: num * 60 });
            }}
          />
          minute(s)
        </div>
      </WithPermissionControlTooltip>
    );
  }

  private _renderNotifyBy(disabled: boolean) {
    const { data, notifyByOptions = [], userAction } = this.props;
    const { notify_by } = data;

    return (
      <WithPermissionControlTooltip userAction={userAction}>
        <Select
          key="notify_by"
          placeholder="Notify by"
          className={cx(this.styles.select, this.styles.control)}
          // @ts-ignore
          value={notify_by}
          disabled={disabled}
          onChange={this._getOnChangeHandler('notify_by')}
          options={notifyByOptions.map((notifyByOption: SelectOption) => ({
            label: notifyByOption.display_name,
            value: notifyByOption.value,
          }))}
        />
      </WithPermissionControlTooltip>
    );
  }

  _renderNote() {
    const { data } = this.props;
    const { notify_by } = data;

    switch (notify_by) {
      case 0:
        return <>{this._renderSlackNote()}</>;

      case 1:
        return <>{this._renderPhoneNote()}</>;

      case 2:
        return <>{this._renderPhoneNote()}</>;

      case 3:
        return <>{this._renderTelegramNote()}</>;

      case 5:
        return <>{this._renderMobileAppNote()}</>;

      case 6:
        return <>{this._renderMobileAppNote()}</>;

      default:
        return null;
    }
  }

  _getOnChangeHandler = (field: string) => {
    return ({ value }: SelectableValue) => {
      const { data, onChange = () => {} } = this.props;
      const { id } = data;

      const newData: NotificationPolicyType = {
        ...prepareNotificationPolicy(data),
        [field]: value,
      };

      onChange(id, newData);
    };
  };

  _getDeleteClickHandler = (id: string) => {
    const { onDelete } = this.props;

    return () => {
      onDelete(id);
    };
  };
}

const getStyles = (_theme: GrafanaTheme2) => {
  return {
    root: css`
      z-index: 1062;
    `,

    step: css`
      display: flex;
      align-items: center;
    `,

    control: css`
      margin-right: 10px;
      flex-shrink: 0;
    `,

    select: css`
      width: 200px !important;
      flex-shrink: 0;
    `,

    delay: css`
      width: 100px !important;
    `,

    container: css`
      width: 200px;
      display: flex;
      align-items: center;
      margin-right: 12px;
    `,
  };
};

export default SortableElement(withTheme2(NotificationPolicy));
