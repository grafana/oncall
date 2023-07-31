import React from 'react';

import { Card, HorizontalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import gitHubStarSVG from 'assets/img/github_star.svg';
import logo from 'assets/img/logo.svg';
import Tag from 'components/Tag/Tag';
import Alerts from 'containers/Alerts/Alerts';
import IRMBanner from 'containers/IRMBanner/IRMBanner';
import { isTopNavbar } from 'plugin/GrafanaPluginRootPage.helpers';
import { useStore } from 'state/useStore';
import { APP_SUBTITLE } from 'utils/consts';

import styles from './Header.module.scss';

const cx = cn.bind(styles);

const Header = observer(() => {
  const store = useStore();

  return (
    <>
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
      <Banners />
    </>
  );

  function renderHeading() {
    if (store.isOpenSource()) {
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

    const { irmPlan } = store.alertGroupStore;

    return (
      <>
        <HorizontalGroup>
          <h1 className={cx('page-header__title')}>Grafana OnCall</h1>
          {irmPlan?.limits && <Tag className={cx('irm-icon')}>{irmPlan.limits.isIrmPro ? 'IRM Pro' : 'IRM Lite'}</Tag>}
        </HorizontalGroup>
        <div className={cx('page-header__sub-title')}>{APP_SUBTITLE}</div>
      </>
    );
  }
});

const Banners: React.FC = () => {
  return (
    <div className={cx('banners')}>
      <Alerts />
      <IRMBanner />
    </div>
  );
};

export default Header;
