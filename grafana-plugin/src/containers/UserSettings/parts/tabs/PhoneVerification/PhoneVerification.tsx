import React, { HTMLAttributes, useCallback, useRef, useState } from 'react';

import { Alert, Button, Field, HorizontalGroup, Icon, Input, Tooltip } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import PluginLink from 'components/PluginLink/PluginLink';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import userSettings from 'containers/UserSettings/UserSettings';
import { WithPermissionControl } from 'containers/WithPermissionControl/WithPermissionControl';
import { User } from 'models/user/user.types';
import { AppFeature } from 'state/features';
import { useStore } from 'state/useStore';
import { UserAction } from 'state/userAction';
import { openErrorNotification } from 'utils';

import styles from './PhoneVerification.module.css';

const cx = cn.bind(styles);

interface PhoneVerificationProps extends HTMLAttributes<HTMLElement> {
  userPk?: User['pk'];
  phone?: string;
}

const PhoneVerification = observer((props: PhoneVerificationProps) => {
  const { phone: propsPhone, userPk: propsUserPk } = props;
  const [phone, setPhone] = useState(propsPhone);
  const [code, setCode] = useState('');
  const [codeSent, setCodeSent] = useState<boolean>(false);

  const codeInputRef = useRef<any>();

  const onChangePhoneCallback = useCallback((event) => {
    setCodeSent(false);
    setPhone(event.target.value);
  }, []);

  const onChangeCodeCallback = useCallback((event) => {
    setCode(event.target.value);
  }, []);

  const store = useStore();
  const { userStore, teamStore } = store;

  const userPk = (propsUserPk || userStore.currentUserPk) as User['pk'];
  const user = userStore.items[userPk as User['pk']];

  const handleMakeTestCallClick = useCallback(() => {
    userStore.makeTestCall(userPk);
  }, [userPk]);

  const handleForgetNumberClick = useCallback(() => {
    userStore.forgetPhone(userPk).then(() => {
      setPhone('');
      userStore.loadUser(userPk);
    });
  }, [userPk]);

  const { isTestCallInProgress } = userStore;

  const onSubmitCallback = useCallback(async () => {
    if (codeSent) {
      userStore
        .verifyPhone(userPk, code)
        .then(() => {
          userStore.loadUser(userPk);
        })
        .catch((error) => {
          openErrorNotification(error.response.data);
        });
    } else {
      await userStore.updateUser({
        pk: userPk,
        email: user.email,
        unverified_phone_number: phone,
      });
      userStore
        .fetchVerificationCode(userPk)
        .then(() => {
          setCodeSent(true);

          if (codeInputRef.current) {
            codeInputRef.current.focus();
          }
        })
        .catch(() => {
          openErrorNotification(
            "Can't send SMS code. Please try other phone number formats. Don't forget the country code!"
          );
        });
    }
  }, [code, codeSent, phone, store, user.email, userPk, userStore]);

  const isPhoneInvalid = !phone || !/^\+\d{8,15}$/.test(phone);

  const twilioConfigured = teamStore.currentTeam?.env_status.twilio_configured;

  const showPhoneInputError = phone && phone.length > 8 && isPhoneInvalid;
  const isCurrent = userStore.currentUserPk === user.pk;
  const action = isCurrent ? UserAction.UpdateOwnSettings : UserAction.UpdateOtherUsersSettings;
  const isButtonDisabled = phone === user.verified_phone_number || (!codeSent && isPhoneInvalid) || !twilioConfigured;

  return (
    <>
      {user.verified_phone_number && (
        <>
          <Alert severity="info" title="You will receive alerts to a new number after verification" />
          <br />
        </>
      )}
      {!twilioConfigured && store.hasFeature(AppFeature.LiveSettings) && (
        <>
          <Alert
            severity="warning"
            // @ts-ignore
            title={
              <>
                Can't verify phone. <PluginLink query={{ page: 'live-settings' }}> Check ENV variables</PluginLink>{' '}
                related to Twilio.
              </>
            }
          />
          <br />
        </>
      )}
      <Field invalid={showPhoneInputError} error={showPhoneInputError ? 'Enter a valid phone number' : null}>
        <WithPermissionControl userAction={action}>
          <Input
            autoFocus
            id="phone"
            required
            disabled={!twilioConfigured}
            placeholder="Please enter the phone number with country code, e.g. +12451111111"
            // @ts-ignore
            prefix={<Icon name="phone" />}
            value={phone}
            onChange={onChangePhoneCallback}
          />
        </WithPermissionControl>
      </Field>
      <Input
        ref={codeInputRef}
        disabled={!codeSent || !store.isUserActionAllowed(action)}
        autoFocus={codeSent}
        onChange={onChangeCodeCallback}
        placeholder="Please enter the code"
      />
      <br />
      <HorizontalGroup>
        <WithPermissionControl userAction={action}>
          <Button variant="primary" onClick={onSubmitCallback} disabled={isButtonDisabled}>
            {codeSent ? 'Verify' : 'Send Code'}
          </Button>
        </WithPermissionControl>
        <WithPermissionControl userAction={action}>
          <WithConfirm title="Are you sure you want to forget this phone number?" confirmText="Forget">
            <Button
              disabled={(!user?.verified_phone_number && !user?.unverified_phone_number) || isTestCallInProgress}
              onClick={handleForgetNumberClick}
              variant="destructive"
            >
              {'Forget Phone Number'}
            </Button>
          </WithConfirm>
        </WithPermissionControl>
        <WithPermissionControl userAction={action}>
          <Button
            disabled={!user?.verified_phone_number || !twilioConfigured || isTestCallInProgress}
            onClick={handleMakeTestCallClick}
          >
            {isTestCallInProgress ? 'Making Test Call...' : 'Make Test Call'}
          </Button>
        </WithPermissionControl>
        <Tooltip content={'Click "Make Test Call" to save a phone number and add it to DnD exceptions.'}>
          <Icon
            name="info-circle"
            style={{
              marginLeft: '10px',
              color: '#1890ff',
            }}
          />
        </Tooltip>
      </HorizontalGroup>
    </>
  );
});

export default PhoneVerification;
