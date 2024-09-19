import React, { FC } from 'react';

import { css } from '@emotion/css';
import { useStyles2, Stack } from '@grafana/ui';
import { StackSize } from 'helpers/consts';

import errorSVG from 'assets/img/error.svg';
import { Text } from 'components/Text/Text';

interface FullPageErrorProps {
  children?: React.ReactNode;
  title?: string;
  subtitle?: React.ReactNode;
}

export const FullPageError: FC<FullPageErrorProps> = ({
  title = 'An unexpected error happened',
  subtitle,
  children,
}) => {
  const styles = useStyles2(getStyles);

  return (
    <div className={styles.wrapper}>
      <Stack direction="column" alignItems="center" gap={StackSize.md}>
        <img src={errorSVG} alt="" />
        <Text.Title level={3}>{title}</Text.Title>
        {subtitle && <Text type="secondary">{subtitle}</Text>}
        {children}
      </Stack>
    </div>
  );
};

const getStyles = () => ({
  wrapper: css`
    margin: 24px auto;
    width: 600px;
    text-align: center;
  `,
});
