import React from 'react';

import { pick } from 'lodash-es';

import { User } from './user.types';

export const getTimezone = (user: User) => {
  return user.timezone || 'UTC';
};

export const getUserNotificationsSummary = (user: User) => {
  if (!user) {
    return null;
  }

  return (
    <>
      Default: {user?.notification_chain_verbal?.default}
      <br />
      Important: {user?.notification_chain_verbal?.important}
    </>
  );
};

export const prepareForUpdate = (user: User) => pick(user, ['pk', 'email']);
