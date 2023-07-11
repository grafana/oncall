import React from 'react';

import { Alert } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import PluginLink from 'components/PluginLink/PluginLink';

import styles from './Maintenance.module.css';

const cx = cn.bind(styles);

interface MaintenancePageProps {}

@observer
class MaintenancePage extends React.Component<MaintenancePageProps> {
  render() {
    return (
      <>
        <Alert
          severity="info"
          className={cx('info-box')}
          // @ts-ignore
          title={
            <>
              To be able to manage maintenance, please go to{' '}
              <PluginLink query={{ page: 'integrations' }}> Integrations page</PluginLink> and select desirable
              integration.
            </>
          }
        />
      </>
    );
  }
}

export default MaintenancePage;
