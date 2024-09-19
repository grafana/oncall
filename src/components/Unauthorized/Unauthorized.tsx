import React, { FC } from 'react';

import { css } from '@emotion/css';
import { GrafanaTheme2, OrgRole } from '@grafana/data';
import { Stack, useStyles2 } from '@grafana/ui';
import { contextSrv } from 'grafana/app/core/core';
import { UserAction } from 'helpers/authorization/authorization';
import { StackSize } from 'helpers/consts';

import { Text } from 'components/Text/Text';

type Props = {
  requiredUserAction: UserAction;
};

export const Unauthorized: FC<Props> = ({ requiredUserAction: { permission, fallbackMinimumRoleRequired } }) => {
  const styles = useStyles2(getStyles);

  return (
    <div className={styles.notFound}>
      <Stack direction="column" gap={StackSize.lg} alignItems="center">
        <Text.Title level={1} className={styles.errorCode}>
          403
        </Text.Title>
        <Text.Title level={4}>
          You do not have access to view this page.{' '}
          {contextSrv.licensedAccessControlEnabled()
            ? `You are missing the ${permission} permission.`
            : `You must be at least a${
                fallbackMinimumRoleRequired === OrgRole.Viewer ? '' : 'n'
              } ${fallbackMinimumRoleRequired}.`}
          <br />
          <br />
          Please contact your organization administrator to request access.
        </Text.Title>
      </Stack>
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
  };
};
