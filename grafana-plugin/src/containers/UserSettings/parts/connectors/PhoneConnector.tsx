import React, { useCallback } from 'react';

import { Alert, Button, HorizontalGroup, InlineField, Input, VerticalGroup, useTheme2 } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import { Tag } from 'components/Tag/Tag';
import { Text } from 'components/Text/Text';
import { WithConfirm } from 'components/WithConfirm/WithConfirm';
import { UserSettingsTab } from 'containers/UserSettings/UserSettings.types';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { AppFeature } from 'state/features';
import { useStore } from 'state/useStore';

import styles from 'containers/UserSettings/parts/UserSettingsParts.module.css';

const cx = cn.bind(styles);

interface PhoneConnectorProps {
  id: ApiSchemas['User']['pk'];
  onTabChange: (tab: UserSettingsTab) => void;
}

export const PhoneConnector = observer((props: PhoneConnectorProps) => {
  const { id, onTabChange } = props;

  const store = useStore();
  const theme = useTheme2();
  const { userStore } = store;

  const storeUser = userStore.items[id];

  const handleClickConfirmPhoneButton = useCallback(() => {
    onTabChange(UserSettingsTab.PhoneVerification);
  }, [storeUser?.unverified_phone_number, onTabChange]);

  const isCurrentUser = storeUser.pk === userStore.currentUserPk;

  const cloudVersionPhone = (user: ApiSchemas['User']) => {
    switch (user.cloud_connection_status) {
      case 0:
        return (
          <>
            <InlineField
              label="Phone"
              labelWidth={12}
              tooltip={'OnCall uses Grafana Cloud OnCall for SMS and phone call notifications'}
            >
              <Button onClick={handleClickConfirmPhoneButton}>Connect to Grafana Cloud OnCall</Button>
            </InlineField>
            <Alert title="This instance is not connected to Grafana Cloud OnCall" severity="warning" />
          </>
        );

      case 1:
        return (
          <>
            <InlineField
              label="Phone"
              labelWidth={12}
              tooltip={'OnCall uses Grafana Cloud OnCall for SMS and phone call notifications'}
            >
              <Button onClick={handleClickConfirmPhoneButton}>Reload from Cloud</Button>
            </InlineField>
            <Alert title="User is not matched with cloud" severity="warning" />
          </>
        );

      case 2:
        return (
          <>
            <InlineField
              label="Phone"
              labelWidth={12}
              tooltip={'OnCall uses Grafana Cloud OnCall for SMS and phone call notifications'}
            >
              <Button onClick={handleClickConfirmPhoneButton}>Verify in Cloud</Button>
            </InlineField>
            <Alert title="Phone number is not verified in Grafana Cloud OnCall" severity="warning" />
          </>
        );
      case 3:
        return (
          <>
            <InlineField
              label="Phone"
              labelWidth={12}
              tooltip={'OnCall uses Grafana Cloud OnCall for SMS and phone call notifications'}
            >
              <Button onClick={handleClickConfirmPhoneButton}>Change in Cloud</Button>
            </InlineField>
            <Alert title="Phone number verified" severity="success" />
          </>
        );
      default:
        return (
          <>
            <InlineField
              label="Phone"
              disabled={true}
              labelWidth={12}
              tooltip={'OnCall uses Grafana Cloud OnCall for SMS and phone call notifications'}
            >
              <Button onClick={handleClickConfirmPhoneButton}>Reload from Cloud</Button>
            </InlineField>
            <Alert title="User is not matched with cloud" severity="warning" />
          </>
        );
    }
  };

  return (
    <div>
      {store.hasFeature(AppFeature.CloudNotifications) ? (
        <>{cloudVersionPhone(storeUser)}</>
      ) : (
        <>
          {storeUser.verified_phone_number ? (
            <div>
              <InlineField label="Phone" labelWidth={12}>
                <HorizontalGroup spacing="xs">
                  <Input disabled={true} value={storeUser.verified_phone_number} />
                  {isCurrentUser ? (
                    <Button variant="secondary" icon="edit" onClick={handleClickConfirmPhoneButton} />
                  ) : (
                    <WithConfirm title="Are you sure you want to edit other's phone number?" confirmText="Proceed">
                      <Button variant="secondary" icon="edit" onClick={handleClickConfirmPhoneButton} />
                    </WithConfirm>
                  )}
                </HorizontalGroup>
              </InlineField>
            </div>
          ) : storeUser.unverified_phone_number ? (
            <VerticalGroup spacing="xs">
              <div className={cx('tag-container')}>
                <Tag
                  color={'rgba(204, 204, 220, 0.04)'}
                  border={theme.colors.border.weak}
                  className={cx('tag', 'tag-left')}
                >
                  <Text type="primary" size="small">
                    Phone
                  </Text>
                </Tag>

                <div className={cx('tag-right')}>
                  <Input disabled={true} value={storeUser.unverified_phone_number} />

                  {isCurrentUser ? (
                    <Button onClick={handleClickConfirmPhoneButton}>Verify</Button>
                  ) : (
                    <WithConfirm title="Are you sure you want to verify other's phone number?" confirmText="Proceed">
                      <Button onClick={handleClickConfirmPhoneButton}>Verify</Button>
                    </WithConfirm>
                  )}
                </div>
              </div>

              <Alert title="Phone number is not verified. Verify or change" severity="warning" />
            </VerticalGroup>
          ) : (
            <div>
              <InlineField label="Phone" labelWidth={12}>
                {isCurrentUser ? (
                  <Button onClick={handleClickConfirmPhoneButton}>Add phone number</Button>
                ) : (
                  <WithConfirm title="Are you sure you want to add other's phone number?" confirmText="Proceed">
                    <Button onClick={handleClickConfirmPhoneButton}>Add phone number</Button>
                  </WithConfirm>
                )}
              </InlineField>
            </div>
          )}
        </>
      )}
    </div>
  );
});
