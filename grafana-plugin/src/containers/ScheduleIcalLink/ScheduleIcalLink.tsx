import React, { FC, useEffect, useState } from 'react';

import { Button, HorizontalGroup, Icon, Label, LoadingPlaceholder, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import CopyToClipboard from 'react-copy-to-clipboard';

import Text from 'components/Text/Text';
import { CreateScheduleExportTokenResponse, Schedule } from 'models/schedule/schedule.types';
import { useStore } from 'state/useStore';
import { openNotification } from 'utils';

import styles from './ScheduleIcalLink.module.css';

const cx = cn.bind(styles);

interface ScheduleICalSettingsProps {
  id: Schedule['id'];
}

const ScheduleICalSettings: FC<ScheduleICalSettingsProps> = observer((props) => {
  const { id } = props;
  const store = useStore();

  const [ICalLink, setICalLink] = useState<string>(undefined);
  const [isiCalLinkExist, setIsICalLinkExist] = useState<boolean>(false);
  const [isICalLinkLoading, setIsICalLinkLoading] = useState<boolean>(true);

  useEffect(() => {
    store.scheduleStore
      .getICalLink(id)
      .then(() => {
        setIsICalLinkExist(true);
        setIsICalLinkLoading(false);
      })
      .catch(() => {
        setIsICalLinkExist(false);
        setIsICalLinkLoading(false);
      });
  }, []);

  const handleCreateICalLink = async () => {
    setIsICalLinkExist(true);
    await store.scheduleStore
      .createICalLink(id)
      .then((res: CreateScheduleExportTokenResponse) => setICalLink(res?.export_url));
  };

  const handleRevokeICalLink = async () => {
    setIsICalLinkExist(false);
    setICalLink(undefined);
    await store.scheduleStore.deleteICalLink(id);
  };

  return (
    <VerticalGroup>
      <Label>iCal link:</Label>
      <Text type="secondary">
        Secret iCal export link to export schedule's on call shifts to Google Calendar, iCal, etc. If you forget it,
        you'll need to revoke this link and create another one.
        <br />
        NOTE: We do not have control over when a client refreshes an imported calendar (e.g. Google Calendar can take up
        to 24hs to reflect schedule changes)
      </Text>
      {isICalLinkLoading ? (
        <LoadingPlaceholder text="Loading..." />
      ) : (
        <>
          {isiCalLinkExist ? (
            <>
              {ICalLink !== undefined ? (
                <VerticalGroup>
                  <HorizontalGroup>
                    <Icon name="exclamation-triangle" />
                    <Text type="warning">Make sure you copy it - you won't be able to access it again.</Text>
                  </HorizontalGroup>
                  <Text className={cx('link-container')}>{ICalLink}</Text>
                  <CopyToClipboard
                    text={ICalLink}
                    onCopy={() => {
                      openNotification('iCal link is copied');
                    }}
                  >
                    <Button icon="copy" variant="secondary">
                      Copy iCal link
                    </Button>
                  </CopyToClipboard>
                </VerticalGroup>
              ) : (
                <VerticalGroup>
                  <Text type="secondary">
                    In case you lost your iCal link you can revoke it and generate a new one.
                  </Text>
                  <Button icon="trash-alt" onClick={handleRevokeICalLink} variant="destructive" fill="outline">
                    Revoke iCal link
                  </Button>
                </VerticalGroup>
              )}
            </>
          ) : (
            <Button icon="plus" onClick={handleCreateICalLink} variant="secondary">
              Create iCal link
            </Button>
          )}
        </>
      )}
    </VerticalGroup>
  );
});

export default ScheduleICalSettings;
