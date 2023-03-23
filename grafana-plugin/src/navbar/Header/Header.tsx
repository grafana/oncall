import React from 'react';

import { Card } from '@grafana/ui';
import cn from 'classnames/bind';

import gitHubStarSVG from 'assets/img/github_star.svg';
import logo from 'img/logo.svg';
import { isTopNavbar } from 'plugin/GrafanaPluginRootPage.helpers';
import { APP_SUBTITLE, GRAFANA_LICENSE_OSS } from 'utils/consts';

import styles from './Header.module.scss';

const cx = cn.bind(styles);

export default function Header({ backendLicense }: { backendLicense: string }) {
  return (
    <div className={cx('root')}>
      <div className={cx('page-header__inner', { 'header-topnavbar': isTopNavbar() })}>
        <div className={cx('navbar-left')}>
          <span className="page-header__logo">
            <img className="page-header__img" src={logo} alt="Grafana OnCall" />
          </span>
          <div className="page-header__info-block">{renderHeading()}</div>
        </div>
      </div>
    </div>
  );

  function renderHeading() {
    if (backendLicense === GRAFANA_LICENSE_OSS) {
      return (
        <div className={cx('heading')}>
          <h1 className={cx('page-header__title')}>Grafana OnCall</h1>
          <div className={cx('navbar-heading-container')}>
            <div className={cx('page-header__sub-title')}>{APP_SUBTITLE}</div>
            <Card heading={undefined} className={cx('navbar-heading')}>
              <a
                href="https://github.com/grafana/oncall"
                className={cx('navbar-link')}
                target="_blank"
                rel="noreferrer"
              >
                <img src={gitHubStarSVG} className={cx('navbar-star-icon')} alt="" /> Star us on GitHub
              </a>
            </Card>
          </div>
        </div>
      );
    }

    return (
      <>
        <h1 className={cx('page-header__title')}>Grafana OnCall</h1>
        <div className={cx('page-header__sub-title')}>{APP_SUBTITLE}</div>
      </>
    );
  }
}
