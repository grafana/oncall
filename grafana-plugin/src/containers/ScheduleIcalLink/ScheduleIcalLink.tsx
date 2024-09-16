import React, { FC, useEffect, useState } from 'react';

import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { Button, Icon, Label, LoadingPlaceholder, Stack, useStyles2 } from '@grafana/ui';
import { openNotification } from 'helpers/helpers';
import { observer } from 'mobx-react';
import CopyToClipboard from 'react-copy-to-clipboard';

import { Text } from 'components/Text/Text';
import { CreateScheduleExportTokenResponse, Schedule } from 'models/schedule/schedule.types';
import { useStore } from 'state/useStore';

interface ScheduleICalSettingsProps {
  id: Schedule['id'];
}

export const ScheduleICalSettings: FC<ScheduleICalSettingsProps> = observer((props) => {
  const { id } = props;
  const store = useStore();
  const styles = useStyles2(getStyles);

  const [ICalLink, setICalLink] = useState<string>(undefined);
  const [isiCalLinkExist, setIsICalLinkExist] = useState(false);
  const [isICalLinkLoading, setIsICalLinkLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        await store.scheduleStore.getICalLink(id);
        setIsICalLinkExist(true);
        setIsICalLinkLoading(false);
      } catch (_err) {
        setIsICalLinkExist(false);
        setIsICalLinkLoading(false);
      }
    })();
  }, []);

  const handleCreateICalLink = async () => {
    setIsICalLinkExist(true);
    const res: CreateScheduleExportTokenResponse = await store.scheduleStore.createICalLink(id);
    setICalLink(res?.export_url);
  };

  const handleRevokeICalLink = async () => {
    setIsICalLinkExist(false);
    setICalLink(undefined);
    await store.scheduleStore.deleteICalLink(id);
  };

  return (
    <Stack direction="column">
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
                <Stack direction="column">
                  <Stack>
                    <Icon name="exclamation-triangle" />
                    <Text type="warning">Make sure you copy it - you won't be able to access it again.</Text>
                  </Stack>
                  <Text className={styles.linkContainer}>{ICalLink}</Text>
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
                </Stack>
              ) : (
                <Stack direction="column">
                  <Text type="secondary">
                    In case you lost your iCal link you can revoke it and generate a new one.
                  </Text>
                  <Button icon="trash-alt" onClick={handleRevokeICalLink} variant="destructive" fill="outline">
                    Revoke iCal link
                  </Button>
                </Stack>
              )}
            </>
          ) : (
            <Button icon="plus" onClick={handleCreateICalLink} variant="secondary">
              Create iCal link
            </Button>
          )}
        </>
      )}
    </Stack>
  );
});

const getStyles = (theme: GrafanaTheme2) => {
  return {
    linkContainer: css`
      background-color: ${theme.colors.background.secondary};
    `,
  };
};
