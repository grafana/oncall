import React, { useCallback } from 'react';

import { Button, Label } from '@grafana/ui';
import cn from 'classnames/bind';

import { UserSettingsTab } from 'containers/UserSettings/UserSettings.types';
import { AppFeature } from 'state/features';
import { useStore } from 'state/useStore';

import styles from './index.module.css';

const cx = cn.bind(styles);

interface SlackConnectorProps {
  onTabChange: (tab: UserSettingsTab) => void;
}

const SlackConnector = (props: SlackConnectorProps) => {
  const { onTabChange } = props;

  const store = useStore();

  const handleClickConfirmMobileAppButton = useCallback(() => {
    onTabChange(UserSettingsTab.MobileAppConnection);
  }, [onTabChange]);

  if (!store.hasFeature(AppFeature.MobileApp)) {
    return null;
  }

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

export default SlackConnector;
