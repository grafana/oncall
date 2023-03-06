import React, { FC } from 'react';

import { PluginPage } from 'PluginPage';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import { AppRootProps } from 'types';

import Alerts from 'containers/Alerts/Alerts';
import { pages } from 'pages';
import { isTopNavbar } from 'plugin/GrafanaPluginRootPage.helpers';
import { DEFAULT_PAGE } from 'utils/consts';

import styles from './DefaultPageLayout.module.scss';

const cx = cn.bind(styles);

interface DefaultPageLayoutProps extends AppRootProps {
  children?: any;
  page: string;
}

const DefaultPageLayout: FC<DefaultPageLayoutProps> = observer((props) => {
  const { children, page } = props;

  if (isTopNavbar()) {
    return renderTopNavbar();
  }

  return renderLegacyNavbar();

  function renderTopNavbar(): JSX.Element {
    const matchingPageNav = (pages[page] || pages[DEFAULT_PAGE]).getPageNav();

    return (
      <PluginPage page={page} pageNav={matchingPageNav}>
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
