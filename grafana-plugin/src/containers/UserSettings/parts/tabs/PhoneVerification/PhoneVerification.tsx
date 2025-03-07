import React, { HTMLAttributes, useCallback, useRef, useReducer } from 'react';

import { css } from '@emotion/css';
import { Alert, Button, Field, Icon, Input, Switch, Tooltip, Stack, useStyles2 } from '@grafana/ui';
import { isUserActionAllowed, UserAction, UserActions } from 'helpers/authorization/authorization';
import { StackSize } from 'helpers/consts';
import { useIsLoading } from 'helpers/hooks';
import { observer } from 'mobx-react';

import { PluginLink } from 'components/PluginLink/PluginLink';
import { RenderConditionally } from 'components/RenderConditionally/RenderConditionally';
import { Text } from 'components/Text/Text';
import { WithPermissionControlDisplay } from 'containers/WithPermissionControl/WithPermissionControlDisplay';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { ActionKey } from 'models/loader/action-keys';
import { UserHelper } from 'models/user/user.helpers';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { AppFeature } from 'state/features';
import { rootStore } from 'state/rootStore';
import { useStore } from 'state/useStore';

interface PhoneVerificationProps extends HTMLAttributes<HTMLElement> {
  userPk?: ApiSchemas['User']['pk'];
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

export const PhoneVerification = observer((props: PhoneVerificationProps) => {
  const { userPk: propsUserPk } = props;
  const store = useStore();
  const { userStore, organizationStore } = store;

  const userPk = (propsUserPk || userStore.currentUserPk) as ApiSchemas['User']['pk'];
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
      phone: user.verified_phone_number || user.unverified_phone_number || '+',
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

  const handleForgetNumberClick = useCallback(async () => {
    await UserHelper.forgetPhone(userPk);
    await userStore.fetchItemById({ userPk });
    setState({ phone: '', showForgetScreen: false, isCodeSent: false, isPhoneCallInitiated: false });
  }, [userPk, UserHelper.forgetPhone, userStore.fetchItemById]);

  const onSubmitCallback = useCallback(
    async (type) => {
      let codeVerification = isCodeSent;
      if (type === 'verification_call') {
        codeVerification = isPhoneCallInitiated;
      }
      if (codeVerification) {
        await UserHelper.verifyPhone(userPk, code);
        userStore.fetchItemById({ userPk });
      } else {
        async function start_verification(token) {
          await userStore.updateUser({
            pk: userPk,
            email: user.email,
            unverified_phone_number: phone,
          });

          switch (type) {
            case 'verification_call':
              await UserHelper.fetchVerificationCall(userPk, token);
              setState({isPhoneCallInitiated: true});
              if (codeInputRef.current) {
                codeInputRef.current.focus();
              }
              break;
            case 'verification_sms':
              await UserHelper.fetchVerificationCode(userPk, token);
              setState({isCodeSent: true});
              if (codeInputRef.current) {
                codeInputRef.current.focus();
              }
              break;
          }
        }

        if (!rootStore.recaptchaSiteKey?.trim()) {
          await start_verification(null)
        } else {
          window.grecaptcha.ready(async function () {
          const token = await window.grecaptcha.execute(rootStore.recaptchaSiteKey, {
            action: 'mobile_verification_code',
          });
            await start_verification(token);
          });
        }
      }
    },
    [
      code,
      isCodeSent,
      phone,
      user.email,
      userPk,
      UserHelper.verifyPhone,
      userStore.updateUser,
      UserHelper.fetchVerificationCode,
    ]
  );

  const onVerifyCallback = useCallback(async () => {
    await UserHelper.verifyPhone(userPk, code);
    userStore.fetchItemById({ userPk });
  }, [code, userPk, UserHelper.verifyPhone, userStore.fetchItemById]);

  const styles = useStyles2(getStyles);

  const providerConfiguration = organizationStore.currentOrganization?.env_status.phone_provider;
  const isPhoneProviderConfigured = providerConfiguration?.configured;

  const phoneHasMinimumLength = phone?.length > 8;

  const isPhoneValid = phoneHasMinimumLength && PHONE_REGEX.test(phone);
  const showPhoneInputError = phoneHasMinimumLength && !isPhoneValid && !isPhoneNumberHidden && !isLoading;

  const action = isCurrentUser ? UserActions.UserSettingsWrite : UserActions.UserSettingsAdmin;
  const isButtonDisabled =
    phone === user.verified_phone_number ||
    (!isCodeSent && !isPhoneValid && !isPhoneCallInitiated) ||
    !isPhoneProviderConfigured ||
    !window.grecaptcha;
  const disabledButtonTooltipText = window.grecaptcha ? undefined : 'reCAPTCHA has not been loaded';

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
      <Stack direction="column">
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
          className={styles.phoneField}
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
            className={styles.phoneField}
          />
        )}
        <Stack gap={StackSize.xs}>
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
        </Stack>
        {showToggle && (
          <div className={styles.switch}>
            <div className={styles.switchIcon}>
              <Switch value={isPhoneNumberHidden} onChange={onTogglePhoneCallback} />
            </div>
            <label>Hide my phone number from teammates</label>
          </div>
        )}

        <PhoneVerificationButtonsGroup
          action={action}
          isCodeSent={isCodeSent}
          isPhoneCallInitiated={isPhoneCallInitiated}
          isButtonDisabled={isButtonDisabled}
          disabledButtonTooltipText={disabledButtonTooltipText}
          providerConfiguration={providerConfiguration}
          onSubmitCallback={onSubmitCallback}
          onVerifyCallback={onVerifyCallback}
          handleMakeTestCallClick={handleMakeTestCallClick}
          handleSendTestSmsClick={handleSendTestSmsClick}
          onShowForgetScreen={() => setState({ showForgetScreen: true })}
          user={user}
        />
      </Stack>
    </WithPermissionControlDisplay>
  );
});

interface ForgetPhoneScreenProps {
  phone: string;
  onCancel(): void;
  onForget(): void;
}

function ForgetPhoneScreen({ phone, onCancel, onForget }: ForgetPhoneScreenProps) {
  const styles = useStyles2(getStyles);

  return (
    <>
      <Text size="large" className={styles.phoneForgetHeading}>
        Do you really want to forget the verified phone number <strong>{phone}</strong> ?
      </Text>
      <Stack justifyContent="flex-end">
        <Button variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button variant="destructive" onClick={onForget}>
          Forget
        </Button>
      </Stack>
    </>
  );
}

interface PhoneVerificationButtonsGroupProps {
  action: UserAction;

  isCodeSent: boolean;
  isPhoneCallInitiated: boolean;
  isButtonDisabled: boolean;
  disabledButtonTooltipText?: string;
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

  user: ApiSchemas['User'];
}

const PhoneVerificationButtonsGroup = observer(
  ({
    action,
    isCodeSent,
    isPhoneCallInitiated,
    isButtonDisabled,
    disabledButtonTooltipText,
    providerConfiguration,
    onSubmitCallback,
    onVerifyCallback,
    handleMakeTestCallClick,
    handleSendTestSmsClick,
    onShowForgetScreen,
    user,
  }: PhoneVerificationButtonsGroupProps) => {
    const isTestCallOrSmsInProgress = useIsLoading(ActionKey.TEST_CALL_OR_SMS);
    const showForgetNumber = !!user.verified_phone_number;
    const showVerifyOrSendCodeButton = !user.verified_phone_number;
    const verificationStarted = isCodeSent || isPhoneCallInitiated;
    return (
      <Stack>
        {showVerifyOrSendCodeButton && (
          <Stack>
            {verificationStarted ? (
              <>
                <WithPermissionControlTooltip userAction={action}>
                  <Button variant="primary" onClick={onVerifyCallback}>
                    Verify
                  </Button>
                </WithPermissionControlTooltip>
              </>
            ) : (
              <RenderConditionally
                shouldRender={Boolean(providerConfiguration)}
                render={() => (
                  <Stack>
                    {providerConfiguration.verification_sms && (
                      <WithPermissionControlTooltip userAction={action}>
                        <Button
                          variant="primary"
                          onClick={() => onSubmitCallback('verification_sms')}
                          disabled={isButtonDisabled}
                          tooltip={disabledButtonTooltipText}
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
                          tooltip={disabledButtonTooltipText}
                        >
                          Call to get the code
                        </Button>
                      </WithPermissionControlTooltip>
                    )}
                  </Stack>
                )}
              ></RenderConditionally>
            )}
          </Stack>
        )}

        {showForgetNumber && (
          <WithPermissionControlTooltip userAction={action}>
            <Button
              disabled={(!user.verified_phone_number && !user.unverified_phone_number) || isTestCallOrSmsInProgress}
              onClick={onShowForgetScreen}
              variant="destructive"
            >
              {'Forget Phone Number'}
            </Button>
          </WithPermissionControlTooltip>
        )}

        {user.verified_phone_number && (
          <Stack>
            {providerConfiguration.test_sms && (
              <WithPermissionControlTooltip userAction={action}>
                <Button
                  disabled={
                    !user?.verified_phone_number || !providerConfiguration.configured || isTestCallOrSmsInProgress
                  }
                  onClick={handleSendTestSmsClick}
                >
                  Send test sms
                </Button>
              </WithPermissionControlTooltip>
            )}
            {providerConfiguration.test_call && (
              <Stack gap={StackSize.xs}>
                <WithPermissionControlTooltip userAction={action}>
                  <Button
                    disabled={
                      !user?.verified_phone_number || !providerConfiguration.configured || isTestCallOrSmsInProgress
                    }
                    onClick={handleMakeTestCallClick}
                  >
                    {isTestCallOrSmsInProgress ? 'Making Test Call...' : 'Make Test Call'}
                  </Button>
                </WithPermissionControlTooltip>
                <Tooltip content={'Click "Make Test Call" to save a phone number and add it to DnD exceptions.'}>
                  <Icon name="info-circle" />
                </Tooltip>
              </Stack>
            )}
          </Stack>
        )}
      </Stack>
    );
  }
);

const getStyles = () => {
  return {
    switch: css`
      display: flex;
      flex-direction: row;
      align-items: center;
    `,

    switchIcon: css`
      margin-right: 12px;
    `,

    phoneField: css`
      width: 100%;
      margin-bottom: 8px;
    `,

    phoneForgetHeading: css`
      display: block;
      margin-bottom: 24px;
    `,
  };
};
