import React from 'react';

import { Card } from '@grafana/ui';
import cn from 'classnames/bind';

import gitHubStarSVG from 'assets/img/github_star.svg';
import GrafanaTeamSelect from 'containers/GrafanaTeamSelect/GrafanaTeamSelect';
import logo from 'img/logo.svg';
import { APP_SUBTITLE, GRAFANA_LICENSE_OSS } from 'utils/consts';

import styles from './Header.module.scss';

const cx = cn.bind(styles);

export default function Header({ page, backendLicense }: { page: string; backendLicense: string }) {
  return (
    <div className="page-container">
      <div className="page-header">
        <div className="page-header__inner">
          <span className="page-header__logo">
            <img className="page-header__img" src={logo} alt="Grafana OnCall" />
          </span>

          <div className="page-header__info-block">{renderHeading()}</div>

          <GrafanaTeamSelect currentPage={page} />
        </div>
      </div>
    </div>
  );

  function renderHeading() {
    const heading = (
      <>
        <h1 className="page-header__title">Grafana OnCall</h1>
        <div className="page-header__sub-title">{APP_SUBTITLE}</div>
      </>
    );

    if (backendLicense === GRAFANA_LICENSE_OSS) {
      return (
        <div className={cx('heading')}>
          {heading}
          <Card heading={undefined} className={cx('navbar-heading')}>
            <a href="https://github.com/grafana/oncall" className={cx('navbar-link')} target="_blank" rel="noreferrer">
              <img src={gitHubStarSVG} className={cx('navbar-star-icon')} alt="" /> Star us on GitHub
            </a>
          </Card>
        </div>
      );
    }

    return heading;
  }
}
