import React, { HTMLAttributes, useCallback, useRef, useReducer } from 'react';

import { Alert, Button, Field, HorizontalGroup, Icon, Input, Switch, Tooltip, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import { WithPermissionControlDisplay } from 'containers/WithPermissionControl/WithPermissionControlDisplay';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { User } from 'models/user/user.types';
import { rootStore } from 'state';
import { AppFeature } from 'state/features';
import { useStore } from 'state/useStore';
import { isUserActionAllowed, UserAction, UserActions } from 'utils/authorization';

import styles from './PhoneVerification.module.css';

const cx = cn.bind(styles);

interface PhoneVerificationProps extends HTMLAttributes<HTMLElement> {
  userPk?: User['pk'];
}

interface PhoneVerificationState {
  phone: string;
  code: string;
  isCodeSent?: boolean;
  isPhoneCallInitiated?: boolean;
  isPhoneNumberHidden: boolean;
  isLoading: boolean;
  showForgetScreen: boolean;
}

const PHONE_REGEX = /^\+\d{8,15}$/;

const PhoneVerification = observer((props: PhoneVerificationProps) => {
  const { userPk: propsUserPk } = props;
  const store = useStore();
  const { userStore, organizationStore } = store;

  const userPk = (propsUserPk || userStore.currentUserPk) as User['pk'];
  const user = userStore.items[userPk];
  const isCurrentUser = userStore.currentUserPk === user.pk;

  const [
    { showForgetScreen, phone, code, isCodeSent, isPhoneCallInitiated, isPhoneNumberHidden, isLoading },
    setState,
  ] = useReducer(
    (state: PhoneVerificationState, newState: Partial<PhoneVerificationState>) => ({
      ...state,
      ...newState,
    }),
    {
      code: '',
      phone: user.verified_phone_number || '+',
      isLoading: false,
      isCodeSent: false,
      isPhoneCallInitiated: false,
      showForgetScreen: false,
      isPhoneNumberHidden: user.hide_phone_number,
    }
  );

  const codeInputRef = useRef<any>();

  const onTogglePhoneCallback = useCallback(
    async ({ currentTarget: { checked: isPhoneNumberHidden } }: React.ChangeEvent<HTMLInputElement>) => {
      setState({ isPhoneNumberHidden, isLoading: true });

      await userStore.updateUser({ pk: userPk, hide_phone_number: isPhoneNumberHidden });

      setState({ phone: user.verified_phone_number, isLoading: false });
    },
    [user, userPk, userStore.updateUser]
  );

  const onChangePhoneCallback = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    setState({ isCodeSent: false, isPhoneCallInitiated: false, phone: event.target.value });
  }, []);

  const onChangeCodeCallback = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    setState({ code: event.target.value });
  }, []);

  const handleMakeTestCallClick = useCallback(() => {
    userStore.makeTestCall(userPk);
  }, [userPk, userStore.makeTestCall]);

  const handleSendTestSmsClick = useCallback(() => {
    userStore.sendTestSms(userPk);
  }, [userPk, userStore.sendTestSms]);

  const handleForgetNumberClick = useCallback(() => {
    userStore.forgetPhone(userPk).then(async () => {
      await userStore.loadUser(userPk);
      setState({ phone: '', showForgetScreen: false, isCodeSent: false, isPhoneCallInitiated: false });
    });
  }, [userPk, userStore.forgetPhone, userStore.loadUser]);

  const onSubmitCallback = useCallback(
    async (type) => {
      let codeVerification = isCodeSent;
      if (type === 'verification_call') {
        codeVerification = isPhoneCallInitiated;
      }
      if (codeVerification) {
        userStore.verifyPhone(userPk, code).then(() => {
          userStore.loadUser(userPk);
        });
      } else {
        window.grecaptcha.ready(function () {
          window.grecaptcha
            .execute(rootStore.recaptchaSiteKey, { action: 'mobile_verification_code' })
            .then(async function (token) {
              await userStore.updateUser({
                pk: userPk,
                email: user.email,
                unverified_phone_number: phone,
              });

              switch (type) {
                case 'verification_call':
                  userStore.fetchVerificationCall(userPk, token).then(() => {
                    setState({ isPhoneCallInitiated: true });
                    if (codeInputRef.current) {
                      codeInputRef.current.focus();
                    }
                  });
                  break;
                case 'verification_sms':
                  userStore.fetchVerificationCode(userPk, token).then(() => {
                    setState({ isCodeSent: true });
                    if (codeInputRef.current) {
                      codeInputRef.current.focus();
                    }
                  });
                  break;
              }
            });
        });
      }
    },
    [
      code,
      isCodeSent,
      phone,
      user.email,
      userPk,
      userStore.verifyPhone,
      userStore.updateUser,
      userStore.fetchVerificationCode,
    ]
  );

  const onVerifyCallback = useCallback(async () => {
    userStore.verifyPhone(userPk, code).then(() => {
      userStore.loadUser(userPk);
    });
  }, [code, userPk, userStore.verifyPhone, userStore.loadUser]);

  const providerConfiguration = organizationStore.currentOrganization?.env_status.phone_provider;
  const isPhoneProviderConfigured = providerConfiguration?.configured;

  const phoneHasMinimumLength = phone?.length > 8;

  const isPhoneValid = phoneHasMinimumLength && PHONE_REGEX.test(phone);
  const showPhoneInputError = phoneHasMinimumLength && !isPhoneValid && !isPhoneNumberHidden && !isLoading;

  const action = isCurrentUser ? UserActions.UserSettingsWrite : UserActions.UserSettingsAdmin;
  const isButtonDisabled =
    phone === user.verified_phone_number ||
    (!isCodeSent && !isPhoneValid && !isPhoneCallInitiated) ||
    !isPhoneProviderConfigured;

  const isPhoneDisabled = !!user.verified_phone_number;
  const isCodeFieldDisabled = (!isCodeSent && !isPhoneCallInitiated) || !isUserActionAllowed(action);
  const showToggle = user.verified_phone_number && isCurrentUser;

  if (showForgetScreen) {
    return (
      <ForgetPhoneScreen
        phone={phone}
        onCancel={() => setState({ showForgetScreen: false })}
        onForget={handleForgetNumberClick}
      />
    );
  }

  return (
    <WithPermissionControlDisplay userAction={UserActions.UserSettingsWrite}>
      <VerticalGroup>
        {isPhoneValid && !user.verified_phone_number && (
          <Alert severity="info" title="You will receive alerts to a new number after verification" />
        )}

        {!isPhoneProviderConfigured && store.hasFeature(AppFeature.LiveSettings) && (
          <>
            <Alert
              severity="warning"
              title={
                (
                  <Text type="primary">
                    Can't verify phone. <PluginLink query={{ page: 'live-settings' }}> Check ENV variables</PluginLink>{' '}
                    to configure your provider.
                  </Text>
                ) as any
              }
            />
          </>
        )}

        <Field
          className={cx('phone__field')}
          invalid={showPhoneInputError}
          error={showPhoneInputError ? 'Enter a valid phone number' : null}
        >
          <WithPermissionControlTooltip userAction={action}>
            <Input
              autoFocus
              id="phone"
              required
              disabled={!isPhoneProviderConfigured || isPhoneDisabled}
              placeholder="Please enter the phone number with country code, e.g. +12451111111"
              prefix={<Icon name={'phone' as any} />}
              value={phone}
              onChange={onChangePhoneCallback}
            />
          </WithPermissionControlTooltip>
        </Field>
        {!user.verified_phone_number && (
          <Input
            ref={codeInputRef}
            disabled={isCodeFieldDisabled}
            autoFocus={isCodeSent}
            onChange={onChangeCodeCallback}
            placeholder="Please enter the code"
            className={cx('phone__field')}
          />
        )}
        <HorizontalGroup spacing="xs">
          <Icon name="info-circle" />
          <Text type="secondary">
            This site is protected by reCAPTCHA and the Google{' '}
            <a target="_blank" rel="noreferrer" href="https://policies.google.com/privacy">
              <Text type="link">Privacy Policy</Text>
            </a>{' '}
            and{' '}
            <a target="_blank" rel="noreferrer" href="https://policies.google.com/terms">
              <Text type="link">Terms of Service </Text>
            </a>{' '}
            apply.
          </Text>
        </HorizontalGroup>
        {showToggle && (
          <div className={cx('switch')}>
            <div className={cx('switch__icon')}>
              <Switch value={isPhoneNumberHidden} onChange={onTogglePhoneCallback} />
            </div>
            <label className={cx('switch__label')}>Hide my phone number from teammates</label>
          </div>
        )}

        <PhoneVerificationButtonsGroup
          action={action}
          isCodeSent={isCodeSent}
          isPhoneCallInitiated={isPhoneCallInitiated}
          isButtonDisabled={isButtonDisabled}
          isTestCallInProgress={userStore.isTestCallInProgress}
          providerConfiguration={providerConfiguration}
          onSubmitCallback={onSubmitCallback}
          onVerifyCallback={onVerifyCallback}
          handleMakeTestCallClick={handleMakeTestCallClick}
          handleSendTestSmsClick={handleSendTestSmsClick}
          onShowForgetScreen={() => setState({ showForgetScreen: true })}
          user={user}
        />
      </VerticalGroup>
    </WithPermissionControlDisplay>
  );
});

interface ForgetPhoneScreenProps {
  phone: string;
  onCancel(): void;
  onForget(): void;
}

function ForgetPhoneScreen({ phone, onCancel, onForget }: ForgetPhoneScreenProps) {
  return (
    <>
      <Text size="large" className={cx('phone__forgetHeading')}>
        Do you really want to forget the verified phone number <strong>{phone}</strong> ?
      </Text>
      <HorizontalGroup justify="flex-end">
        <Button variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button variant="destructive" onClick={onForget}>
          Forget
        </Button>
      </HorizontalGroup>
    </>
  );
}

interface PhoneVerificationButtonsGroupProps {
  action: UserAction;

  isCodeSent: boolean;
  isPhoneCallInitiated: boolean;
  isButtonDisabled: boolean;
  isTestCallInProgress: boolean;
  providerConfiguration: {
    configured: boolean;
    test_call: boolean;
    test_sms: boolean;
    verification_call: boolean;
    verification_sms: boolean;
  };
  onSubmitCallback(type: string): void;
  onVerifyCallback(): void;
  handleMakeTestCallClick(): void;
  handleSendTestSmsClick(): void;
  onShowForgetScreen(): void;

  user: User;
}

function PhoneVerificationButtonsGroup({
  action,
  isCodeSent,
  isPhoneCallInitiated,
  isButtonDisabled,
  isTestCallInProgress,
  providerConfiguration,
  onSubmitCallback,
  onVerifyCallback,
  handleMakeTestCallClick,
  handleSendTestSmsClick,
  onShowForgetScreen,
  user,
}: PhoneVerificationButtonsGroupProps) {
  const showForgetNumber = !!user.verified_phone_number;
  const showVerifyOrSendCodeButton = !user.verified_phone_number;
  const verificationStarted = isCodeSent || isPhoneCallInitiated;
  return (
    <HorizontalGroup>
      {showVerifyOrSendCodeButton && (
        <HorizontalGroup>
          {verificationStarted ? (
            <>
              <WithPermissionControlTooltip userAction={action}>
                <Button variant="primary" onClick={onVerifyCallback}>
                  Verify
                </Button>
              </WithPermissionControlTooltip>
            </>
          ) : (
            <HorizontalGroup>
              {providerConfiguration.verification_sms && (
                <WithPermissionControlTooltip userAction={action}>
                  <Button
                    variant="primary"
                    onClick={() => onSubmitCallback('verification_sms')}
                    disabled={isButtonDisabled}
                  >
                    Send Code
                  </Button>
                </WithPermissionControlTooltip>
              )}
              {providerConfiguration.verification_call && (
                <WithPermissionControlTooltip userAction={action}>
                  <Button
                    variant="primary"
                    onClick={() => onSubmitCallback('verification_call')}
                    disabled={isButtonDisabled}
                  >
                    Call to get the code
                  </Button>
                </WithPermissionControlTooltip>
              )}
            </HorizontalGroup>
          )}
        </HorizontalGroup>
      )}

      {showForgetNumber && (
        <WithPermissionControlTooltip userAction={action}>
          <Button
            disabled={(!user.verified_phone_number && !user.unverified_phone_number) || isTestCallInProgress}
            onClick={onShowForgetScreen}
            variant="destructive"
          >
            {'Forget Phone Number'}
          </Button>
        </WithPermissionControlTooltip>
      )}

      {user.verified_phone_number && (
        <HorizontalGroup>
          {providerConfiguration.test_sms && (
            <WithPermissionControlTooltip userAction={action}>
              <Button
                disabled={!user?.verified_phone_number || !providerConfiguration.configured || isTestCallInProgress}
                onClick={handleSendTestSmsClick}
              >
                Send test sms
              </Button>
            </WithPermissionControlTooltip>
          )}
          {providerConfiguration.test_call && (
            <HorizontalGroup spacing="xs">
              <WithPermissionControlTooltip userAction={action}>
                <Button
                  disabled={!user?.verified_phone_number || !providerConfiguration.configured || isTestCallInProgress}
                  onClick={handleMakeTestCallClick}
                >
                  {isTestCallInProgress ? 'Making Test Call...' : 'Make Test Call'}
                </Button>
              </WithPermissionControlTooltip>
              <Tooltip content={'Click "Make Test Call" to save a phone number and add it to DnD exceptions.'}>
                <Icon name="info-circle" />
              </Tooltip>
            </HorizontalGroup>
          )}
        </HorizontalGroup>
      )}
    </HorizontalGroup>
  );
}

export default PhoneVerification;
