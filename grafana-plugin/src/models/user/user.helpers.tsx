import React from 'react';

import { Tooltip } from '@grafana/ui';
import dayjs from 'dayjs';
import { pick } from 'lodash-es';

import { Timezone } from 'models/timezone/timezone.types';

import { User, UserRole } from './user.types';

export const getIconType = (role: UserRole) => {
  switch (role) {
    case UserRole.ADMIN:
      return 'crown';
    case UserRole.EDITOR:
      return 'user';
    case UserRole.VIEWER:
      return 'eye';
    default:
      return 'user';
  }
};

export const getRole = (role: UserRole) => {
  switch (role) {
    case UserRole.ADMIN:
      return 'Admin';
    case UserRole.EDITOR:
      return 'Editor';
    case UserRole.VIEWER:
      return 'Viewer';
    default:
      return '';
  }
};

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
