import React, { useCallback } from 'react';

import { Button, Label } from '@grafana/ui';
import cn from 'classnames/bind';

import { UserSettingsTab } from 'containers/UserSettings/UserSettings.types';

import styles from './index.module.css';

const cx = cn.bind(styles);

interface MobileAppConnectorProps {
  onTabChange: (tab: UserSettingsTab) => void;
}

const MobileAppConnector = (props: MobileAppConnectorProps) => {
  const { onTabChange } = props;

  const handleClickConfirmMobileAppButton = useCallback(() => {
    onTabChange(UserSettingsTab.MobileAppConnection);
  }, [onTabChange]);

  return (
    <div className={cx('user-item')}>
      <Label>Mobile App:</Label>
      <div>
        <Button size="sm" fill="text" onClick={handleClickConfirmMobileAppButton}>
          Click to add a mobile app
        </Button>
      </div>
    </div>
  );
};

export default MobileAppConnector;
