import React, { HTMLAttributes, useCallback, useEffect, useRef, useReducer } from 'react';

import { Alert, Button, Field, HorizontalGroup, Icon, Input, Switch, Tooltip, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import PluginLink from 'components/PluginLink/PluginLink';
import WithConfirm from 'components/WithConfirm/WithConfirm';
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
}

interface PhoneVerificationState {
  phone: string;
  code: string;
  isCodeSent: boolean;
  isPhoneNumberHidden: boolean;
  isLoading: boolean;
}

const PHONE_REGEX = /^\+\d{8,15}$/;

const PhoneVerification = observer((props: PhoneVerificationProps) => {
  const { userPk: propsUserPk } = props;

  const store = useStore();
  const { userStore, teamStore } = store;

  const userPk = (propsUserPk || userStore.currentUserPk) as User['pk'];
  let user = userStore.items[userPk];

  const [{ phone, code, isCodeSent, isPhoneNumberHidden, isLoading }, setState] = useReducer(
    (state: PhoneVerificationState, newState: Partial<PhoneVerificationState>) => ({
      ...state,
      ...newState,
    }),
    {
      code: '',
      phone: user.verified_phone_number || '+',
      isLoading: false,
      isCodeSent: false,
      isPhoneNumberHidden: user.hide_phone_number,
    }
  );

  const codeInputRef = useRef<any>();

  const onTogglePhoneCallback = useCallback(
    async ({ currentTarget: { checked: isPhoneNumberHidden } }: React.ChangeEvent<HTMLInputElement>) => {
      setState({ isPhoneNumberHidden, isLoading: true });

      await userStore.updateUser({ pk: userPk, hide_phone_number: isPhoneNumberHidden });
      user = userStore.items[userPk];

      setState({ phone: user.verified_phone_number, isLoading: false });
    },
    []
  );

  const onChangePhoneCallback = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    setState({ isCodeSent: false, phone: event.target.value });
  }, []);

  const onChangeCodeCallback = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    setState({ code: event.target.value });
  }, []);

  const handleMakeTestCallClick = useCallback(() => {
    userStore.makeTestCall(userPk);
  }, [userPk]);

  const handleForgetNumberClick = useCallback(() => {
    userStore.forgetPhone(userPk).then(() => {
      setState({ phone: '' });
      userStore.loadUser(userPk);
    });
  }, [userPk]);

  const { isTestCallInProgress } = userStore;

  const onSubmitCallback = useCallback(async () => {
    if (isCodeSent) {
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
          setState({ isCodeSent: true });

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
  }, [code, isCodeSent, phone, store, user.email, userPk, userStore]);

  const isTwilioConfigured = teamStore.currentTeam?.env_status.twilio_configured;

  const isPhoneValid = phone?.length > 8 && PHONE_REGEX.test(phone);
  const showPhoneInputError = phone && !isPhoneValid && !isPhoneNumberHidden && !isLoading;

  const isCurrent = userStore.currentUserPk === user.pk;
  const action = isCurrent ? UserAction.UpdateOwnSettings : UserAction.UpdateOtherUsersSettings;
  const isButtonDisabled =
    phone === user.verified_phone_number || (!isCodeSent && !isPhoneValid) || !isTwilioConfigured;

  return (
    <>
      {user.verified_phone_number && (
        <>
          <Alert severity="info" title="You will receive alerts to a new number after verification" />
          <br />
        </>
      )}

      {!isTwilioConfigured && store.hasFeature(AppFeature.LiveSettings) && (
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

      <VerticalGroup>
        <Field
          className={cx('phone__field')}
          invalid={showPhoneInputError}
          error={showPhoneInputError ? 'Enter a valid phone number' : null}
        >
          <WithPermissionControl userAction={action}>
            <Input
              autoFocus
              id="phone"
              required
              disabled={!isTwilioConfigured}
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
          disabled={!isCodeSent || !store.isUserActionAllowed(action)}
          autoFocus={isCodeSent}
          onChange={onChangeCodeCallback}
          placeholder="Please enter the code"
          className={cx('phone__field')}
        />

        {user.verified_phone_number && (
          <div className={cx('switch')}>
            <div className={cx('switch__icon')}>
              <Switch value={isPhoneNumberHidden} onChange={onTogglePhoneCallback} />
            </div>
            <label className={cx('switch__label')}>Hide my phone number from public view</label>
          </div>
        )}
      </VerticalGroup>

      <br />

      <PhoneVerificationButtonsGroup
        action={action}
        isCodeSent={isCodeSent}
        isButtonDisabled={isButtonDisabled}
        isTestCallInProgress={isTestCallInProgress}
        isTwilioConfigured={isTwilioConfigured}
        onSubmitCallback={onSubmitCallback}
        handleForgetNumberClick={handleForgetNumberClick}
        handleMakeTestCallClick={handleMakeTestCallClick}
        user={user}
      />
    </>
  );
});

interface PhoneVerificationButtonsGroupProps {
  action: UserAction.UpdateOwnSettings | UserAction.UpdateOtherUsersSettings;

  isCodeSent: boolean;
  isButtonDisabled: boolean;
  isTestCallInProgress: boolean;
  isTwilioConfigured: boolean;

  onSubmitCallback(): void;
  handleForgetNumberClick(): void;
  handleMakeTestCallClick(): void;

  user: User;
}

function PhoneVerificationButtonsGroup({
  action,
  isCodeSent,
  isButtonDisabled,
  isTestCallInProgress,
  isTwilioConfigured,
  onSubmitCallback,
  handleForgetNumberClick,
  handleMakeTestCallClick,
  user,
}: PhoneVerificationButtonsGroupProps) {
  const showForgetNumber = !!user.verified_phone_number;
  const showVerifyOrSendCodeButton = !user.verified_phone_number;

  return (
    <HorizontalGroup>
      {showVerifyOrSendCodeButton && (
        <WithPermissionControl userAction={action}>
          <Button variant="primary" onClick={onSubmitCallback} disabled={isButtonDisabled}>
            {isCodeSent ? 'Verify' : 'Send Code'}
          </Button>
        </WithPermissionControl>
      )}

      {showForgetNumber && (
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
      )}

      <WithPermissionControl userAction={action}>
        <Button
          disabled={!user?.verified_phone_number || !isTwilioConfigured || isTestCallInProgress}
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
  );
}

export default PhoneVerification;
