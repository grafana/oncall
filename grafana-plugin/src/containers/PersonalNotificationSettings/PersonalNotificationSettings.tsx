import React, { useCallback } from 'react';

import { Button, HorizontalGroup, Icon, LoadingPlaceholder, Tooltip } from '@grafana/ui';
import cn from 'classnames/bind';
import { get } from 'lodash-es';
import { observer } from 'mobx-react';

import NotificationPolicy from 'components/Policy/NotificationPolicy';
import SortableList from 'components/SortableList/SortableList';
import Text from 'components/Text/Text';
import Timeline from 'components/Timeline/Timeline';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { NotificationPolicyType } from 'models/notification_policy';
import { User as UserType } from 'models/user/user.types';
import { AppFeature } from 'state/features';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization';

import { getColor } from './PersonalNotificationSettings.helpers';
import img from './img/default-step.png';

import styles from './PersonalNotificationSettings.module.css';

const cx = cn.bind(styles);

interface PersonalNotificationSettingsProps {
  userPk: UserType['pk'];
  isImportant: boolean;
}

const PersonalNotificationSettings = observer((props: PersonalNotificationSettingsProps) => {
  const { userPk, isImportant } = props;
  const store = useStore();
  const { userStore } = store;

  const getNotificationPolicySortEndHandler = useCallback(
    (indexOffset: number) => {
      return ({ oldIndex, newIndex }: any) => {
        userStore.moveNotificationPolicyToPosition(userPk, oldIndex, newIndex, indexOffset);
      };
    },
    [userPk, userStore]
  );

  const getAddNotificationPolicyHandler = useCallback(() => {
    return () => {
      userStore.addNotificationPolicy(userPk, isImportant);
    };
  }, [isImportant, userPk, userStore]);

  const getNotificationPolicyUpdateHandler = useCallback(
    (id: NotificationPolicyType['id'], data) => {
      userStore.updateNotificationPolicy(userPk, id, data);
    },
    [userPk, userStore]
  );

  const getNotificationPolicyDeleteHandler = useCallback(
    (id: NotificationPolicyType['id']) => {
      userStore.deleteNotificationPolicy(userPk, id);
    },
    [userPk, userStore]
  );

  const allNotificationPolicies = userStore.notificationPolicies[userPk];

  const title = (
    <Text.Title level={5}>
      <HorizontalGroup>
        {isImportant ? 'Important Notifications' : 'Default Notifications'}
        <Tooltip
          placement="top"
          content={
            <>
              Trigger different notification policies from escalation setup (page "Integrations"). <img src={img} />
            </>
          }
        >
          <Icon name="info-circle" size="md"></Icon>
        </Tooltip>
      </HorizontalGroup>
    </Text.Title>
  );

  if (!allNotificationPolicies) {
    return (
      <div className={cx('root')}>
        {title}
        <LoadingPlaceholder text="Loading..." />
      </div>
    );
  }

  const notificationPolicies =
    allNotificationPolicies &&
    allNotificationPolicies.filter(
      (notificationPolicy: NotificationPolicyType) => notificationPolicy.important === isImportant
    );

  const offset = isImportant
    ? allNotificationPolicies.findIndex((notificationPolicy: NotificationPolicyType) => notificationPolicy.important)
    : 0;

  const isCurrent = store.userStore.currentUserPk === userPk;

  const user = userStore.items[userPk];

  const userAction = isCurrent ? UserActions.UserSettingsWrite : UserActions.NotificationSettingsWrite;
  const getPhoneStatus = () => {
    if (store.hasFeature(AppFeature.CloudNotifications)) {
      return user.cloud_connection_status;
    }
    return Number(user.verified_phone_number) + 2;
  };

  // Mobile app related NotificationPolicy props
  const isMobileAppConnected = user.messaging_backends['MOBILE_APP']?.connected;
  const showCloudConnectionWarning =
    store.hasFeature(AppFeature.CloudConnection) && !store.cloudStore.cloudConnectionStatus.cloud_connection_status;

  return (
    <div className={cx('root')}>
      {title}
      {/* @ts-ignore */}
      <SortableList
        helperClass={cx('sortable-helper')}
        className={cx('steps')}
        axis="y"
        lockAxis="y"
        onSortEnd={getNotificationPolicySortEndHandler(offset)}
        useDragHandle
      >
        {notificationPolicies.map((notificationPolicy: NotificationPolicyType, index: number) => (
          <NotificationPolicy
            // @ts-ignore
            userAction={userAction}
            key={notificationPolicy.id}
            index={index}
            number={index + 1}
            telegramVerified={Boolean(user.telegram_configuration)}
            phoneStatus={getPhoneStatus()}
            isMobileAppConnected={isMobileAppConnected}
            showCloudConnectionWarning={showCloudConnectionWarning}
            slackTeamIdentity={store.organizationStore.currentOrganization?.slack_team_identity}
            slackUserIdentity={user.slack_user_identity}
            data={notificationPolicy}
            onChange={getNotificationPolicyUpdateHandler}
            onDelete={getNotificationPolicyDeleteHandler}
            notificationChoices={get(userStore.notificationChoices, 'step.choices', [])}
            waitDelays={get(userStore.notificationChoices, 'wait_delay.choices', [])}
            notifyByOptions={userStore.notifyByOptions}
            color={getColor(index)}
            store={store}
          />
        ))}
        <Timeline.Item number={notificationPolicies.length + 1} backgroundColor={getColor(notificationPolicies.length)}>
          <div className={cx('step')}>
            <WithPermissionControlTooltip userAction={userAction}>
              <Button icon="plus" variant="secondary" fill="text" onClick={getAddNotificationPolicyHandler()}>
                Add Notification Step
              </Button>
            </WithPermissionControlTooltip>
          </div>
        </Timeline.Item>
      </SortableList>
    </div>
  );
});

export default PersonalNotificationSettings;
