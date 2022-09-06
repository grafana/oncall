import React, { FC } from 'react';

import { Icon, Tooltip } from '@grafana/ui';
import cn from 'classnames/bind';
import MediaQuery from 'react-responsive';

import styles from './Policy.module.css';

const cx = cn.bind(styles);

interface PolicyNoteProps {
  type?: 'success' | 'info' | 'danger';
  children?: any;
}

function getIcon(type: PolicyNoteProps['type']) {
  switch (type) {
    case 'success':
      return <Icon size="lg" className={cx('note-icon')} name="check-circle" style={{ color: 'green' }} />;
    case 'danger':
      return <Icon size="lg" className={cx('note-icon')} name="exclamation-triangle" style={{ color: 'orange' }} />;
    default:
      return <Icon size="lg" className={cx('note-icon')} name="info-circle" style={{ color: '#1890ff' }} />;
  }
}

const PolicyNote: FC<PolicyNoteProps> = (props) => {
  const { children, type = 'info' } = props;

  const icon = getIcon(type);

  return (
    // TODO fix
    <MediaQuery maxWidth={0}>
      {(matches: boolean) =>
        matches ? (
          <>
            {icon}
            {children}
          </>
        ) : (
          <>
            <Tooltip placement="top" content={children as string}>
              {icon}
            </Tooltip>
          </>
        )
      }
    </MediaQuery>
  );
};

export default PolicyNote;
