import React, { useEffect } from 'react';

import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { VerticalGroup, useStyles2 } from '@grafana/ui';

import { PluginLink } from 'components/PluginLink/PluginLink';
import { Text } from 'components/Text/Text';
import { openWarningNotification } from 'utils/utils';

export interface PageBaseState {
  errorData: PageErrorData;
}

export interface PageErrorData {
  isNotFoundError?: boolean;
  isWrongTeamError?: boolean;
  isUnknownError?: boolean;
  wrongTeamNoPermissions?: boolean;
  switchToTeam?: { name: string; id: string };
}

export const PageErrorHandlingWrapper = function ({
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
  const styles = useStyles2(getStyles);

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
    <div className={styles.notFound}>
      <VerticalGroup spacing="lg" align="center">
        <Text.Title level={1} className={styles.errorCode}>
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
};

const getStyles = (theme: GrafanaTheme2) => {
  return {
    notFound: css`
      margin: 50px auto;
      text-align: center;
      width: 400px;
    `,

    errorCode: css`
      color: ${theme.colors.warning.text};
    `,

    changeTeamIcon: css`
      color: white;
      margin-right: 4px;
      padding-top: 6px;
    `,
  };
};
