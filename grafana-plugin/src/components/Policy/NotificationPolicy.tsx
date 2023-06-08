import React from 'react';

import { SelectableValue } from '@grafana/data';
import { Button, IconButton, Select } from '@grafana/ui';
import cn from 'classnames/bind';
import { SortableElement } from 'react-sortable-hoc';

import PluginLink from 'components/PluginLink/PluginLink';
import Timeline from 'components/Timeline/Timeline';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { Channel } from 'models/channel';
import { NotificationPolicyType, prepareNotificationPolicy } from 'models/notification_policy';
import { NotifyBy } from 'models/notify_by';
import { User } from 'models/user/user.types';
import { WaitDelay } from 'models/wait_delay';
import { RootStore } from 'state';
import { AppFeature } from 'state/features';
import { UserAction } from 'utils/authorization';

import DragHandle from './DragHandle';
import PolicyNote from './PolicyNote';

import styles from './NotificationPolicy.module.css';

const cx = cn.bind(styles);

export interface NotificationPolicyProps {
  data: NotificationPolicyType;
  slackTeamIdentity?: {
    general_log_channel_pk: Channel['id'];
  };
  slackUserIdentity?: User['slack_user_identity'];
  onChange: (id: NotificationPolicyType['id'], value: NotificationPolicyType) => void;
  onDelete: (id: string) => void;
  notificationChoices: any[];
  channels?: any[];
  waitDelays?: WaitDelay[];
  notifyByOptions?: NotifyBy[];
  telegramVerified: boolean;
  phoneStatus: number;
  isMobileAppConnected: boolean;
  showCloudConnectionWarning: boolean;
  color: string;
  number: number;
  userAction: UserAction;
  store: RootStore;
}

export class NotificationPolicy extends React.Component<NotificationPolicyProps, any> {
  render() {
    const { data, notificationChoices, number, color, userAction } = this.props;
    const { id, step } = data;

    return (
      <Timeline.Item className={cx('root')} number={number} backgroundColor={color}>
        <div className={cx('step')}>
          <WithPermissionControlTooltip disableByPaywall userAction={userAction}>
            <DragHandle />
          </WithPermissionControlTooltip>
          <WithPermissionControlTooltip disableByPaywall userAction={userAction}>
            <Select
              className={cx('select', 'control')}
              onChange={this._getOnChangeHandler('step')}
              value={step}
              options={notificationChoices.map((option: any) => ({ label: option.display_name, value: option.value }))}
            />
          </WithPermissionControlTooltip>
          {this._renderControls()}
          <WithPermissionControlTooltip userAction={userAction}>
            <IconButton
              className={cx('control')}
              name="trash-alt"
              onClick={this._getDeleteClickHandler(id)}
              variant="secondary"
            />
          </WithPermissionControlTooltip>
          {this._renderNote()}
        </div>
      </Timeline.Item>
    );
  }

  _renderControls() {
    const { data } = this.props;
    const { step } = data;

    switch (step) {
      case 0:
        return <>{this._renderWaitDelays()}</>;

      case 1:
        return <>{this._renderNotifyBy()}</>;

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

  private _renderWaitDelays() {
    const { data, waitDelays = [], userAction } = this.props;
    const { wait_delay } = data;

    return (
      <WithPermissionControlTooltip userAction={userAction} disableByPaywall>
        <Select
          key="wait-delay"
          placeholder="Wait Delay"
          className={cx('select', 'control')}
          // @ts-ignore
          value={wait_delay}
          onChange={this._getOnChangeHandler('wait_delay')}
          options={waitDelays.map((waitDelay: WaitDelay) => ({
            label: waitDelay.display_name,
            value: waitDelay.value,
          }))}
        />
      </WithPermissionControlTooltip>
    );
  }

  private _renderNotifyBy() {
    const { data, notifyByOptions = [], userAction } = this.props;
    const { notify_by } = data;

    return (
      <WithPermissionControlTooltip userAction={userAction} disableByPaywall>
        <Select
          key="notify_by"
          placeholder="Notify by"
          className={cx('select', 'control')}
          // @ts-ignore
          value={notify_by}
          onChange={this._getOnChangeHandler('notify_by')}
          options={notifyByOptions.map((notifyByOption: NotifyBy) => ({
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

export default SortableElement(NotificationPolicy);
