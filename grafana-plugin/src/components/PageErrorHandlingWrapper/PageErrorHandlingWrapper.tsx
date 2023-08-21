import React, { useEffect } from 'react';

import { VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';

import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import { openWarningNotification } from 'utils';

import styles from './PageErrorHandlingWrapper.module.css';

const cx = cn.bind(styles);

export interface PageBaseState {
  errorData: PageErrorData;
}

export interface PageErrorData {
  isNotFoundError?: boolean;
  isWrongTeamError?: boolean;
  wrongTeamNoPermissions?: boolean;
  switchToTeam?: { name: string; id: string };
}

export default function PageErrorHandlingWrapper({
  errorData,
  objectName,
  pageName,
  itemNotFoundMessage,
  children,
}: {
  errorData?: PageErrorData;
  objectName?: string;
  pageName: string;
  itemNotFoundMessage?: string;
  children: () => React.ReactNode;
}): JSX.Element {
  useEffect(() => {
    if (!errorData) {
      return;
    }
    const { isWrongTeamError, isNotFoundError } = errorData;
    if (!isWrongTeamError && isNotFoundError && itemNotFoundMessage) {
      openWarningNotification(itemNotFoundMessage);
    }
  }, [errorData?.isNotFoundError]);

  if (!errorData || !errorData.isWrongTeamError) {
    return <>{children()}</>;
  }

  const { wrongTeamNoPermissions } = errorData;

  return (
    <div className={cx('not-found')}>
      <VerticalGroup spacing="lg" align="center">
        <Text.Title level={1} className={cx('error-code')}>
          403
        </Text.Title>
        {wrongTeamNoPermissions && (
          <Text.Title level={4}>
            This {objectName} belongs to a team you are not a part of, or this team hasn't shared access with you.
            Please contact your organization administrator to request access to the team.
          </Text.Title>
        )}
        <Text type="secondary">
          Or return to the <PluginLink query={{ page: pageName }}>{objectName} list</PluginLink>
        </Text>
      </VerticalGroup>
    </div>
  );
}
