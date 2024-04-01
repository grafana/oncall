import React from 'react';

import { GrafanaTheme2 } from '@grafana/data';
import { css, cx } from '@emotion/css';
import { useStyles2 } from '@grafana/ui';

interface IntegrationBlockItemProps {
  children: React.ReactNode;
}

export const IntegrationBlockItem: React.FC<IntegrationBlockItemProps> = (props) => {
  const styles = useStyles2(getStyles);

  return (
    <div className={cx(styles.parent)} data-testid="integration-block-item">
      <div className={cx(styles.content)}>{props.children}</div>
    </div>
  );
};

const getStyles = (_theme: GrafanaTheme2) => {
  return {
    parent: css`
      display: flex;
      flex-direction: row;
      margin-bottom: 4px;
      max-width: 100%;
    `,

    content: css`
      width: 100%;
      padding-top: 12px;
      padding-bottom: 12px;
    `,
  };
};
