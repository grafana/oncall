import React, { useEffect, useState } from 'react';

import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import { Text } from 'components/Text/Text';
import { MSTeamsInstructions } from 'containers/MSTeams/MSTeamsInstructions';
import { UserHelper } from 'models/user/user.helpers';
import { useStore } from 'state/useStore';

import styles from 'containers/UserSettings/parts/tabs/MSTeamsInfo/MSTeamsInfo.module.css';

const cx = cn.bind(styles);

export const MSTeamsInfo = observer(() => {
  const { userStore, msteamsChannelStore } = useStore();

  const [verificationCode, setVerificationCode] = useState<string>();
  const [onCallisAdded, setOnCallisAdded] = useState(false);

  useEffect(() => {
    (async () => {
      const res = await UserHelper.fetchBackendConfirmationCode(userStore.currentUserPk, 'MSTEAMS');
      setVerificationCode(res);

      await msteamsChannelStore.updateItems();

      const connectedChannels = msteamsChannelStore.getSearchResult();
      if (connectedChannels?.length) {
        setOnCallisAdded(true);
      }
    })();
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
