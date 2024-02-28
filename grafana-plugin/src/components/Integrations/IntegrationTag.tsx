import React, { FC } from 'react';

import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { useStyles2 } from '@grafana/ui';

import { Tag } from 'components/Tag/Tag';
import { Text } from 'components/Text/Text';

interface IntegrationTagProps {
  children: React.ReactNode;
}

export const IntegrationTag: FC<IntegrationTagProps> = ({ children }) => {
  const styles = useStyles2(getStyles);

  return (
    <Tag className={styles.tag}>
      <Text type="primary" size="small" className={styles.radius}>
        {children}
      </Text>
    </Tag>
  );
};

export const getStyles = (theme: GrafanaTheme2) => ({
  tag: css({
    height: '25px',
    background: theme.colors.background.secondary,
    border: `1px solid ${theme.colors.border.weak}`,
  }),
  radius: css({
    borderRadius: '4px',
  }),
});
