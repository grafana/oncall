import React from 'react';

import { cx } from '@emotion/css';
import { Card, HorizontalGroup, useStyles2 } from '@grafana/ui';
import { observer } from 'mobx-react';

import gitHubStarSVG from 'assets/img/github_star.svg';
import logo from 'assets/img/logo.svg';
import { Alerts } from 'containers/Alerts/Alerts';
import { isTopNavbar } from 'plugin/GrafanaPluginRootPage.helpers';
import { useStore } from 'state/useStore';
import { APP_SUBTITLE } from 'utils/consts';

import { getHeaderStyles } from './Header.styles';

export const Header = observer(() => {
  const store = useStore();
  const styles = useStyles2(getHeaderStyles);

  return (
    <>
      <div>
        <div className={cx('page-header__inner', { [styles.headerTopNavbar]: isTopNavbar() })}>
          <div className={cx(styles.navbarLeft)}>
            <span className={cx('page-header__logo', styles.logoContainer)}>
              <img className={cx(styles.pageHeaderImage)} src={logo} alt="Grafana OnCall" />
            </span>
            <div className={cx('page-header__info-block')}>{renderHeading()}</div>
          </div>
        </div>
      </div>
      <Banners />
    </>
  );

  function renderHeading() {
    if (store.isOpenSource) {
      return (
        <div className={cx('heading')}>
          <h1 className={cx(styles.pageHeaderTitle)}>Grafana OnCall</h1>
          <div className={cx(styles.navbarHeadingContainer)}>
            <div className={cx('page-header__sub-title')}>{APP_SUBTITLE}</div>

            <Card heading={undefined} className={cx(styles.navbarHeading)}>
              <a
                href="https://github.com/grafana/oncall"
                className={cx(styles.navbarLink)}
                target="_blank"
                rel="noreferrer"
              >
                <img src={gitHubStarSVG} className={cx(styles.navbarStarIcon)} alt="" /> Star us on GitHub
              </a>
            </Card>
          </div>
        </div>
      );
    }

    return (
      <>
        <HorizontalGroup>
          <h1 className={cx(styles.pageHeaderTitle)}>Grafana OnCall</h1>
        </HorizontalGroup>
        <div className={cx('page-header__sub-title')}>{APP_SUBTITLE}</div>
      </>
    );
  }
});

const Banners: React.FC = () => {
  const styles = useStyles2(getHeaderStyles);
  return (
    <div className={cx(styles.banners)}>
      <Alerts />
    </div>
  );
};
