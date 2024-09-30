import React, { FC } from 'react';

import { cx } from '@emotion/css';
import { Icon, Tooltip, useStyles2 } from '@grafana/ui';
import MediaQuery from 'react-responsive';
import { bem } from 'styles/utils.styles';

import { getPolicyStyles } from './Policy.styles';

interface PolicyNoteProps {
  type?: 'success' | 'info' | 'danger';
  children?: any;
}

function getIcon(type: PolicyNoteProps['type'], styles: ReturnType<typeof getPolicyStyles>) {
  switch (type) {
    case 'success':
      return <Icon size="lg" className={cx(styles.noteIcon, [bem(styles.noteIcon, 'green')])} name="check-circle" />;
    case 'danger':
      return (
        <Icon size="lg" className={cx(styles.noteIcon, [bem(styles.noteIcon, 'orange')])} name="exclamation-triangle" />
      );
    default:
      return <Icon size="lg" className={cx(styles.noteIcon, [bem(styles.noteIcon, 'default')])} name="info-circle" />;
  }
}

export const PolicyNote: FC<PolicyNoteProps> = (props) => {
  const { children, type = 'info' } = props;
  const styles = useStyles2(getPolicyStyles);

  const icon = getIcon(type, styles);

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
