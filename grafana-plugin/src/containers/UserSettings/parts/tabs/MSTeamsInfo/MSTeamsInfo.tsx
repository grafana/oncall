import React, { useEffect, useState } from 'react';

import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import { Text } from 'components/Text/Text';
import MSTeamsInstructions from 'containers/MSTeams/MSTeamsInstructions';
import { useStore } from 'state/useStore';

import styles from 'containers/UserSettings/parts/tabs/MSTeamsInfo/MSTeamsInfo.module.css';

const cx = cn.bind(styles);

export const MSTeamsInfo = observer(() => {
  const { userStore, msteamsChannelStore } = useStore();

  const [verificationCode, setVerificationCode] = useState<string>();
  const [onCallisAdded, setOnCallisAdded] = useState(false);

  useEffect(() => {
    userStore.sendBackendConfirmationCode(userStore.currentUserPk, 'MSTEAMS').then(setVerificationCode);
    msteamsChannelStore.updateItems().then(() => {
      const connectedChannels = msteamsChannelStore.getSearchResult();
      if (connectedChannels?.length) {
        setOnCallisAdded(true);
      }
    });
  }, []);

  useEffect(() => {
    return () => {
      userStore.loadCurrentUser();
    };
  }, []);

  return (
    <>
      <Text.Title level={2} className={cx('heading')}>
        Connect MS Teams workspace
      </Text.Title>
      <MSTeamsInstructions
        personalSettings
        onCallisAdded={onCallisAdded}
        showInfoBox
        verificationCode={verificationCode}
      />
    </>
  );
});
