import React from 'react';

import { Card } from '@grafana/ui';
import cn from 'classnames/bind';

import gitHubStarSVG from 'assets/img/github_star.svg';
import { APP_SUBTITLE, GRAFANA_LICENSE_OSS } from 'utils/consts';

import styles from './NavBarSubtitle.module.css';

const cx = cn.bind(styles);

function NavBarSubtitle({ backendLicense }: { backendLicense: string }) {
  if (backendLicense === GRAFANA_LICENSE_OSS) {
    return (
      <div className={cx('navbar-container')}>
        {APP_SUBTITLE}
        <Card heading={undefined} className={cx('navbar-heading')}>
          <a href="https://github.com/grafana/oncall" className={cx('navbar-link')} target="_blank" rel="noreferrer">
            <img src={gitHubStarSVG} className={cx('navbar-star-icon')} alt="" /> Star us on GitHub
          </a>
        </Card>
      </div>
    );
  }

  return <>{APP_SUBTITLE}</>;
}

export default NavBarSubtitle;
