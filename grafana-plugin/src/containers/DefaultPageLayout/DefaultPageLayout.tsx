import React, { FC } from 'react';

import { css } from '@emotion/css';
import { AppRootProps, NavModelItem } from '@grafana/data';
import { useStyles2 } from '@grafana/ui';
import { PluginPage } from 'PluginPage';
import { observer } from 'mobx-react';


interface DefaultPageLayoutProps extends AppRootProps {
  children?: any;
  page: string;
  pageNav: NavModelItem;
}

export const DefaultPageLayout: FC<DefaultPageLayoutProps> = observer((props) => {
  const { children, page, pageNav } = props;
  const styles = useStyles2(getStyles);

  return (
    <PluginPage page={page} pageNav={pageNav as any}>
      <div className={styles.root}>{children}</div>
    </PluginPage>
  );
});

const getStyles = () => {
  return {
    root: css`
      width: 100%;
      height: 100%;
      display: flex;
      flex-direction: column;

      .filter-table td {
        white-space: break-spaces;
        line-height: 20px;
        height: auto;
      }
    `,
  };
};
