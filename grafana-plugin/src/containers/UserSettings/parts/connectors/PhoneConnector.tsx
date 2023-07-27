import React, { useCallback } from 'react';

import { Alert, Button, HorizontalGroup, InlineField, Input } from '@grafana/ui';

import WithConfirm from 'components/WithConfirm/WithConfirm';
import { UserSettingsTab } from 'containers/UserSettings/UserSettings.types';
import { User } from 'models/user/user.types';
import { AppFeature } from 'state/features';
import { useStore } from 'state/useStore';

interface PhoneConnectorProps {
  id: User['pk'];
  onTabChange: (tab: UserSettingsTab) => void;
}

const PhoneConnector = (props: PhoneConnectorProps) => {
  const { id, onTabChange } = props;

  const store = useStore();
  const { userStore } = store;

  const storeUser = userStore.items[id];

  const handleClickConfirmPhoneButton = useCallback(() => {
    onTabChange(UserSettingsTab.PhoneVerification);
  }, [storeUser?.unverified_phone_number, onTabChange]);

  const isCurrentUser = storeUser.pk === userStore.currentUserPk;

  const cloudVersionPhone = (user: User) => {
    switch (user.cloud_connection_status) {
      case 0:
        return (
          <>
            <InlineField
              label="Phone"
              labelWidth={12}
              tooltip={'OnCall uses Grafana Cloud for SMS and phone call notifications'}
            >
              <Button onClick={handleClickConfirmPhoneButton}>Connect to Cloud</Button>
            </InlineField>
            <Alert title="This instance is not connected to Cloud OnCall" severity="warning" />
          </>
        );

      case 1:
        return (
          <>
            <InlineField
              label="Phone"
              labelWidth={12}
              tooltip={'OnCall uses Grafana Cloud for SMS and phone call notifications'}
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
              tooltip={'OnCall uses Grafana Cloud for SMS and phone call notifications'}
            >
              <Button onClick={handleClickConfirmPhoneButton}>Verify in Cloud</Button>
            </InlineField>
            <Alert title="Phone number is not verified in Grafana Cloud" severity="warning" />
          </>
        );
      case 3:
        return (
          <>
            <InlineField
              label="Phone"
              labelWidth={12}
              tooltip={'OnCall uses Grafana Cloud for SMS and phone call notifications'}
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
              tooltip={'OnCall uses Grafana Cloud for SMS and phone call notifications'}
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
            <div>
              <InlineField label="Phone" labelWidth={12}>
                <HorizontalGroup spacing="xs">
                  <Input disabled={true} value={storeUser.unverified_phone_number} />
                  {isCurrentUser ? (
                    <Button onClick={handleClickConfirmPhoneButton}>Verify</Button>
                  ) : (
                    <WithConfirm title="Are you sure you want to verify other's phone number?" confirmText="Proceed">
                      <Button onClick={handleClickConfirmPhoneButton}>Verify</Button>
                    </WithConfirm>
                  )}
                </HorizontalGroup>
              </InlineField>
              <Alert title="Phone number is not verified. Verify or change" severity="warning" />
            </div>
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
};

export default PhoneConnector;
