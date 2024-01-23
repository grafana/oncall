import Tag from 'components/Tag/Tag';
import Text from 'components/Text/Text';
import { css } from '@emotion/css';

import React, { FC } from 'react';
import { getVar } from 'utils/DOM';
import { useStyles2 } from '@grafana/ui';

interface IntegrationTagProps {
  children: React.ReactNode;
}

const IntegrationTag: FC<IntegrationTagProps> = ({ children }) => {
  const styles = useStyles2(getStyles);

  return (
    <Tag color={getVar('--tag-secondary-transparent')} border={getVar('--border-weak')} className={styles.tag}>
      <Text type="primary" size="small" className={styles.radius}>
        {children}
      </Text>
    </Tag>
  );
};

export const getStyles = () => ({
  tag: css({
    height: '25px',
  }),
  radius: css({
    borderRadius: '4px',
  }),
});

export default IntegrationTag;
