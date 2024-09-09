import React, { FC, ReactElement } from 'react';

import { css } from '@emotion/css';
import { NavModelItem } from '@grafana/data';
import { useStyles2 } from '@grafana/ui';
import { PluginPage } from 'PluginPage';
import { observer } from 'mobx-react';
import { AppRootProps } from 'types';

import { Alerts } from 'containers/Alerts/Alerts';
import { isTopNavbar } from 'plugin/GrafanaPluginRootPage.helpers';

interface DefaultPageLayoutProps extends AppRootProps {
  children?: any;
  page: string;
  pageNav: NavModelItem;
}

export const DefaultPageLayout: FC<DefaultPageLayoutProps> = observer((props) => {
  const { children, page, pageNav } = props;
  const styles = useStyles2(getStyles);

  if (isTopNavbar()) {
    return renderTopNavbar();
  }

  return renderLegacyNavbar();

  function renderTopNavbar(): ReactElement {
    return (
      <PluginPage page={page} pageNav={pageNav as any}>
        <div className={styles.root}>{children}</div>
      </PluginPage>
    );
  }

  function renderLegacyNavbar(): ReactElement {
    return (
      <PluginPage page={page}>
        <div className={cx('page-container', css`u-height-100`)}>
          <div className={cx(styles.root)}>
            <Alerts />
            {children}
          </div>
        </div>
      </PluginPage>
    );
  }
});

const getStyles = () => {
  return {
    root: css`
      width: 100%;
      height: 100%;
      display: flex;
      flex-direction: column;

      :global(.filter-table) td {
        white-space: break-spaces;
        line-height: 20px;
        height: auto;
      }
    `,
  };
};
