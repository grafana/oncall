import MailSlurp, { GetPhoneNumbersPhoneCountryEnum, PhoneNumberProjection } from 'mailslurp-client';

import { MAILSLURP_API_KEY } from './constants';

const mailslurp = new MailSlurp({ apiKey: MAILSLURP_API_KEY });

// get a phone number from mailslurp for testing purposes
export const getPhoneNumber = async (): Promise<PhoneNumberProjection> => {
  const {
    content: [phoneNumber],
  } = await mailslurp.phoneController.getPhoneNumbers({
    size: 1,
    phoneCountry: GetPhoneNumbersPhoneCountryEnum.US,
  });
  return phoneNumber;
};

export const waitForSms = async (phoneNumber: PhoneNumberProjection): Promise<string> => {
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
  console.log('GOT THE FUCKING SMS', sms);
  return sms.body;
};

export const getVerificationCodeFromSms = (smsBody: string): string => /\D*(\d*)/.exec(smsBody)[1];
