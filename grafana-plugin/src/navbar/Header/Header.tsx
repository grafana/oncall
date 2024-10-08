import React from 'react';

import { cx } from '@emotion/css';
import { Card, Stack, useStyles2 } from '@grafana/ui';
import { APP_SUBTITLE, IS_CURRENT_ENV_OSS } from 'helpers/consts';
import { observer } from 'mobx-react';

import gitHubStarSVG from 'assets/img/github_star.svg';
import logo from 'assets/img/logo.svg';
import { Alerts } from 'containers/Alerts/Alerts';

import { getHeaderStyles } from './Header.styles';

export const Header = observer(() => {
  const styles = useStyles2(getHeaderStyles);

  return (
    <>
      <div>
        <div className={cx('page-header__inner', styles.headerTopNavbar)}>
          <div className={styles.navbarLeft}>
            <span className={cx('page-header__logo', styles.logoContainer)}>
              <img className={styles.pageHeaderImage} src={logo} alt="Grafana OnCall" />
            </span>
            <div className={cx('page-header__info-block')}>{renderHeading()}</div>
          </div>
        </div>
      </div>
      <Banners />
    </>
  );

  function renderHeading() {
    if (IS_CURRENT_ENV_OSS) {
      return (
        <div className={cx('heading')}>
          <h1 className={styles.pageHeaderTitle}>Grafana OnCall</h1>
          <div className={styles.navbarHeadingContainer}>
            <div className={cx('page-header__sub-title')}>{APP_SUBTITLE}</div>

            <Card heading={undefined} className={styles.navbarHeading}>
              <a
                href="https://github.com/grafana/oncall"
                className={styles.navbarLink}
                target="_blank"
                rel="noreferrer"
              >
                <img src={gitHubStarSVG} className={styles.navbarStarIcon} alt="" /> Star us on GitHub
              </a>
            </Card>
          </div>
        </div>
      );
    }

    return (
      <>
        <Stack>
          <h1 className={styles.pageHeaderTitle}>Grafana OnCall</h1>
        </Stack>
        <div className={cx('page-header__sub-title')}>{APP_SUBTITLE}</div>
      </>
    );
  }
});

const Banners: React.FC = () => {
  const styles = useStyles2(getHeaderStyles);
  return (
    <div className={styles.banners}>
      <Alerts />
    </div>
  );
};
