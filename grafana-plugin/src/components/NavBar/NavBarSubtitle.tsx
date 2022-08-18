import React from 'react';
import cn from 'classnames/bind';

import { Card, Icon } from '@grafana/ui';

import { APP_SUBTITLE } from 'utils/consts';

import styles from './NavBarSubtitle.module.css';

const cx = cn.bind(styles);

function NavBarSubtitle() {
  return (
    <div className={cx('navbar-container')}>
      {APP_SUBTITLE}
      <Card heading={undefined} className={cx('navbar-heading')}>
        <a href="https://github.com/grafana/oncall">
          <Icon name="star" className={cx('navbar-star-icon')} /> Star us on GitHub
        </a>
      </Card>
    </div>
  );
}

export default NavBarSubtitle;
