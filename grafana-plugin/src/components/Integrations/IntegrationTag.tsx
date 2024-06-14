import React, { FC } from 'react';

import { css } from '@emotion/css';
import { useStyles2 } from '@grafana/ui';

import { Tag, TagColor } from 'components/Tag/Tag';
import { Text } from 'components/Text/Text';

interface IntegrationTagProps {
  children: React.ReactNode;
}

export const IntegrationTag: FC<IntegrationTagProps> = ({ children }) => {
  const styles = useStyles2(getStyles);

  return (
    <Tag className={styles.tag} color={TagColor.SECONDARY}>
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
