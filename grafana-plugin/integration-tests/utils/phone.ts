import MailSlurp, { GetPhoneNumbersPhoneCountryEnum, PhoneNumberProjection } from 'mailslurp-client';

import { MAILSLURP_API_KEY } from './constants';

const _getPhoneNumber = (): (() => Promise<PhoneNumberProjection>) => {
  let cachedPhoneNumber: PhoneNumberProjection;

  const __getPhoneNumber = async () => {
    if (cachedPhoneNumber) {
      return cachedPhoneNumber;
    }

    const mailslurp = new MailSlurp({ apiKey: MAILSLURP_API_KEY });

    const {
      content: [phoneNumber],
    } = await mailslurp.phoneController.getPhoneNumbers({
      size: 1,
      phoneCountry: GetPhoneNumbersPhoneCountryEnum.US,
    });

    return phoneNumber;
  };

  return __getPhoneNumber;
};

export const getPhoneNumber = _getPhoneNumber();

export const waitForSms = async (): Promise<string> => {
  const mailslurp = new MailSlurp({ apiKey: MAILSLURP_API_KEY });
  const phoneNumber = await getPhoneNumber();

  const [sms] = await mailslurp.waitController.waitForSms({
    waitForSmsConditions: {
      count: 1,
      unreadOnly: true,
      // only start waiting for smses that would've been received after this function has been invoked
      since: new Date(),
      phoneNumberId: phoneNumber.id,
      timeout: 30_000,
    },
  });
  return sms.body;
};

export const getVerificationCodeFromSms = (smsBody: string): string => /\D*(\d*)/.exec(smsBody)[1];
