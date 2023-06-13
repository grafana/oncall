import React, { useEffect, useState } from 'react';

import { Button, Icon, Label, LoadingPlaceholder } from '@grafana/ui';
import cn from 'classnames/bind';
import CopyToClipboard from 'react-copy-to-clipboard';

import Text from 'components/Text/Text';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { User } from 'models/user/user.types';
import { useStore } from 'state/useStore';
import { openNotification } from 'utils';
import { UserActions } from 'utils/authorization';

import styles from './index.module.css';

const cx = cn.bind(styles);

// eslint-disable-next-line @typescript-eslint/naming-convention
interface ICalConnectorProps {
  id: User['pk'];
}

const ICalConnector = (props: ICalConnectorProps) => {
  const { id } = props;

  const store = useStore();
  const { userStore } = store;

  const [showiCalLink, setShowiCalLink] = useState<string>(undefined);
  const [isiCalLinkExisting, setIsiCalLinkExisting] = useState<boolean>(false);
  const [iCalLoading, setiCalLoading] = useState<boolean>(true);

  useEffect(() => {
    userStore
      .getiCalLink(id)
      .then((_res) => {
        setIsiCalLinkExisting(true);
        setiCalLoading(false);
      })
      .catch((_res) => {
        setIsiCalLinkExisting(false);
        setiCalLoading(false);
      });
  }, []);

  const handleCreateiCalLink = async () => {
    setIsiCalLinkExisting(true);
    await userStore.createiCalLink(id).then((res) => setShowiCalLink(res?.export_url));
  };

  const handleRevokeiCalLink = async () => {
    setIsiCalLinkExisting(false);
    setShowiCalLink(undefined);
    await userStore.deleteiCalLink(id);
  };

  return (
    <div className={cx('user-item')}>
      <Label>iCal link:</Label>
      <Text type="secondary">
        Secret iCal export link to add your assigned on call shifts to your calendar.
        <br />
        NOTE: We do not have control over when a client refreshes an imported calendar.
      </Text>
      <div className={cx('iCal-settings')}>
        {iCalLoading ? (
          <LoadingPlaceholder text="Loading..." />
        ) : (
          <>
            {isiCalLinkExisting ? (
              <>
                {showiCalLink !== undefined ? (
                  <>
                    <div className={cx('iCal-link-container')}>
                      <Icon name="exclamation-triangle" className={cx('warning-icon')} />{' '}
                      <Text type="warning">Make sure you copy it - you won't be able to access it again.</Text>
                      <div className={cx('iCal-link')}>{showiCalLink}</div>
                    </div>
                    <CopyToClipboard
                      text={showiCalLink}
                      onCopy={() => {
                        openNotification('iCal link is copied');
                      }}
                    >
                      <Button icon="copy" variant="secondary" className={cx('iCal-button')}>
                        Copy iCal link
                      </Button>
                    </CopyToClipboard>
                  </>
                ) : (
                  <>
                    <Text type="secondary">
                      In case you lost your iCal link you can revoke it and generate a new one.
                    </Text>
                    <WithPermissionControlTooltip userAction={UserActions.UserSettingsWrite}>
                      <Button
                        icon="trash-alt"
                        onClick={handleRevokeiCalLink}
                        className={cx('iCal-button')}
                        variant="destructive"
                        fill="outline"
                      >
                        Revoke iCal link
                      </Button>
                    </WithPermissionControlTooltip>
                  </>
                )}
              </>
            ) : (
              <WithPermissionControlTooltip userAction={UserActions.UserSettingsWrite}>
                <Button icon="plus" onClick={handleCreateiCalLink} className={cx('iCal-button')} variant="secondary">
                  Create iCal link
                </Button>
              </WithPermissionControlTooltip>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default ICalConnector;
