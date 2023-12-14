import React, { FC } from 'react';

import { NavModelItem } from '@grafana/data';
import { PluginPage } from 'PluginPage';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import { AppRootProps } from 'types';

import Alerts from 'containers/Alerts/Alerts';
import { isTopNavbar } from 'plugin/GrafanaPluginRootPage.helpers';

import styles from './DefaultPageLayout.module.scss';

const cx = cn.bind(styles);

interface DefaultPageLayoutProps extends AppRootProps {
  children?: any;
  page: string;
  pageNav: NavModelItem;
}

const DefaultPageLayout: FC<DefaultPageLayoutProps> = observer((props) => {
  const { children, page, pageNav } = props;

  if (isTopNavbar()) {
    return renderTopNavbar();
  }

  return renderLegacyNavbar();

  function renderTopNavbar(): JSX.Element {
    return (
      <PluginPage page={page} pageNav={pageNav}>
        <div className={cx('root')}>{children}</div>
      </PluginPage>
    );
  }

  function renderLegacyNavbar(): JSX.Element {
    return (
      <PluginPage page={page}>
        <div className="page-container u-height-100">
          <div className={cx('root', 'navbar-legacy')}>
            <Alerts />
            {children}
          </div>
        </div>
      </PluginPage>
    );
  }
});

export default DefaultPageLayout;
