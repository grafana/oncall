import { Locator, Page } from '@playwright/test';

import { clickButton, fillInInputByPlaceholderValue, selectDropdownValue } from './forms';
import { closeModal } from './modals';
import { goToOnCallPage } from './navigation';
import { getPhoneNumber, getVerificationCodeFromSms, waitForSms } from './phone';

type NotifyBy = 'SMS' | 'Phone call';

const openUserSettingsModal = async (page: Page): Promise<void> => {
  await goToOnCallPage(page, 'users');
  await clickButton({ page, buttonText: 'View my profile' });
  await page.locator('text=To edit user details such as Username, email, and role').waitFor({ state: 'visible' });
};

const getForgetPhoneNumberButton = (page: Page): Locator => page.locator('button >> text=Forget Phone Number');

export const verifyUserPhoneNumber = async (page: Page): Promise<void> => {
  // open the user settings modal
  await openUserSettingsModal(page);

  // go to the Phone Verification tab
  await page.locator('a[aria-label="Tab Phone Verification"]').click();

  // check to see if we've already verified our phone number.. no need to do it more than once
  if (await getForgetPhoneNumberButton(page).isVisible()) {
    await closeModal(page);
    return;
  }

  // get the phone number we will use
  const phoneNumber = await getPhoneNumber();

  /**
   * input the phone number and submit the form
   * on the backend this should trigger twilio to send out an SMS verification code
   */
  await fillInInputByPlaceholderValue(page, 'Please enter the phone number with country code', phoneNumber.phoneNumber);
  await clickButton({ page, buttonText: 'Send Code' });

  // wait for the SMS verification code to arrive
  const sms = await waitForSms();

  // take the SMS verification code that we just received, input it into the form, and submit the form
  await fillInInputByPlaceholderValue(page, 'Please enter the code', getVerificationCodeFromSms(sms));
  await clickButton({ page, buttonText: 'Verify' });

  // wait for a confirmation that the number has been verified and then close the modal
  await getForgetPhoneNumberButton(page).click();
  await closeModal(page);
};

/**
 * gets the first row of our default notification settings
 * and then gets the notification type dropdown
 */
const getFirstDefaultNotificationSettingTypeDropdown = async (page: Page): Promise<Locator> => {
  const defaultNotificationSettingsList = page.locator('ul[class*="Timeline-module"] >> nth=0');
  await defaultNotificationSettingsList.waitFor({ state: 'visible' });

  const firstDefaultNotificationSettingRow = defaultNotificationSettingsList.locator('li >> nth=0');
  await firstDefaultNotificationSettingRow.waitFor({ state: 'visible' });

  // get the notification type dropdown specifically
  return firstDefaultNotificationSettingRow.locator('div[class*="input-wrapper"] >> nth=1');
};

export const configureUserNotificationSettings = async (page: Page, notifyBy: NotifyBy): Promise<void> => {
  // open the user settings modal
  await openUserSettingsModal(page);

  /**
   * see if we already have a default notification setting
   * if we don't click the Add Notification Step button and add one
   * otherwise update the existing one
   */
  const defaultNotificationsAddNotificationStepButton = page.locator(
    'div[class*="PersonalNotificationSettings"] >> nth=0 text=Add Notification Step'
  );
  if (await defaultNotificationsAddNotificationStepButton.isVisible()) {
    await defaultNotificationsAddNotificationStepButton.click();
  }

  // select our notification type
  const firstDefaultNotificationTypeDropdopdown = await getFirstDefaultNotificationSettingTypeDropdown(page);
  await selectDropdownValue({
    page,
    value: notifyBy,
    selectType: 'grafanaSelect',
    startingLocator: firstDefaultNotificationTypeDropdopdown,
    optionExactMatch: false, // there are emojis at the end
  });

  // close the modal
  await closeModal(page);
};
