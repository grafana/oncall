import React, { FC } from 'react';

import { OrgRole } from '@grafana/data';
import { VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { contextSrv } from 'grafana/app/core/core';

import Text from 'components/Text/Text';
import { UserAction } from 'utils/authorization';

import styles from './Unauthorized.module.css';

const cx = cn.bind(styles);

type Props = {
  requiredUserAction: UserAction;
};

const Unauthorized: FC<Props> = ({ requiredUserAction: { permission, fallbackMinimumRoleRequired } }) => (
  <div className={cx('not-found')}>
    <VerticalGroup spacing="lg" align="center">
      <Text.Title level={1} className={cx('error-code')}>
        403
      </Text.Title>
      <Text.Title level={4}>
        You do not have access to view this page.{' '}
        {contextSrv.accessControlEnabled()
          ? `You are missing the ${permission} permission.`
          : `You must be at least a${
              fallbackMinimumRoleRequired === OrgRole.Viewer ? '' : 'n'
            } ${fallbackMinimumRoleRequired}.`}
        <br />
        <br />
        Please contact your organization administrator to request access.
      </Text.Title>
    </VerticalGroup>
  </div>
);

export default Unauthorized;
