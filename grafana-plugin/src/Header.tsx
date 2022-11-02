import React from 'react';

import GrafanaTeamSelect from 'containers/GrafanaTeamSelect/GrafanaTeamSelect';

import { APP_SUBTITLE } from 'utils/consts';

import logo from 'img/logo.svg';

export default function Header({ page }: { page: string }) {
  return (
    <div className="page-container">
      <div className="page-header">
        <div className="page-header__inner">
          <span className="page-header__logo">
            <img className="page-header__img" src={logo} alt="Grafana OnCall" />
          </span>

          <div className="page-header__info-block">
            <h1 className="page-header__title">Grafana OnCall</h1>
            <div className="page-header__sub-title">{APP_SUBTITLE}</div>
          </div>

          <GrafanaTeamSelect currentPage={page} />
        </div>
      </div>
    </div>
  );
}
