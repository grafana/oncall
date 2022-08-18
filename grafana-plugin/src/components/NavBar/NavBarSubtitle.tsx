import React from 'react';

import cn from 'classnames/bind';
import { Card, Icon } from '@grafana/ui';
import { APP_SUBTITLE } from 'utils/consts';

import gitHubStarSVG from 'assets/img/github_star.svg';

import styles from './NavBarSubtitle.module.css';

const cx = cn.bind(styles);

function NavBarSubtitle() {
  return (
    <div className={cx('navbar-container')}>
      {APP_SUBTITLE}
      <Card heading={undefined} className={cx('navbar-heading')}>
        <a href="https://github.com/grafana/oncall" className={cx('navbar-link')} target="_blank">
          <img src={gitHubStarSVG} className={cx('navbar-star-icon')} alt='' /> Star us on GitHub
        </a>
      </Card>
    </div>
  );
}

export default NavBarSubtitle;
