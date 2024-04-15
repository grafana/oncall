import React, { useEffect, useState } from 'react';

import { Alert, Button, HorizontalGroup, InlineField, Input, LoadingPlaceholder, Tooltip } from '@grafana/ui';
import CopyToClipboard from 'react-copy-to-clipboard';

import { WithConfirm } from 'components/WithConfirm/WithConfirm';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { UserHelper } from 'models/user/user.helpers';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization/authorization';
import { openNotification } from 'utils/utils';

// eslint-disable-next-line @typescript-eslint/naming-convention
interface ICalConnectorProps {
  id: ApiSchemas['User']['pk'];
}

export const ICalConnector = (props: ICalConnectorProps) => {
  const { id } = props;
  const store = useStore();
  const [showiCalLink, setShowiCalLink] = useState<string>(undefined);
  const [isiCalLinkExisting, setIsiCalLinkExisting] = useState<boolean>(false);
  const [iCalLoading, setiCalLoading] = useState<boolean>(true);

  useEffect(() => {
    (async () => {
      try {
        await UserHelper.getiCalLink(id);
        setIsiCalLinkExisting(true);
        setiCalLoading(false);
      } catch (_err) {
        setIsiCalLinkExisting(false);
        setiCalLoading(false);
      }
    })();
  }, []);

  const handleCreateiCalLink = async () => {
    setIsiCalLinkExisting(true);
    const res = await UserHelper.createiCalLink(id);
    setShowiCalLink(res?.export_url);
  };

  const handleRevokeiCalLink = async () => {
    setIsiCalLinkExisting(false);
    setShowiCalLink(undefined);
    await UserHelper.deleteiCalLink(id);
  };

  const isCurrentUser = id === store.userStore.currentUserPk;

  return (
    <>
      {iCalLoading ? (
        <LoadingPlaceholder text="Loading..." />
      ) : (
        <>
          {isiCalLinkExisting ? (
            <>
              {showiCalLink !== undefined ? (
                <>
                  <InlineField
                    label="iCal link"
                    labelWidth={12}
                    tooltip={'Secret iCal export link to add your assigned on call shifts to your calendar'}
                  >
                    <HorizontalGroup spacing="xs">
                      <Tooltip content={'In case you lost your iCal link you can revoke it and generate a new one.'}>
                        <Input disabled value={showiCalLink} />
                      </Tooltip>
                      <CopyToClipboard
                        text={showiCalLink}
                        onCopy={() => {
                          openNotification('iCal link is copied');
                        }}
                      >
                        <Button icon="copy" data-testid="copy-ical-link">
                          Copy
                        </Button>
                      </CopyToClipboard>
                    </HorizontalGroup>
                  </InlineField>
                  <Alert severity="warning" title="Make sure you copy it - you won't be able to access it again." />
                </>
              ) : (
                <>
                  <WithPermissionControlTooltip userAction={UserActions.UserSettingsWrite}>
                    <InlineField
                      label="iCal link"
                      labelWidth={12}
                      tooltip={'Secret iCal export link to add your assigned on call shifts to your calendar'}
                    >
                      <HorizontalGroup spacing="xs">
                        <Tooltip content={'In case you lost your iCal link you can revoke it and generate a new one.'}>
                          <Input value={'***'} />
                        </Tooltip>
                        <WithConfirm
                          title={
                            'Are you sure you want to revoke iCal link' + (!isCurrentUser ? ' for other user' : '')
                          }
                          confirmText="Revoke"
                        >
                          <Button
                            icon="trash-alt"
                            variant="destructive"
                            onClick={handleRevokeiCalLink}
                            data-testid="revoke-ical-link"
                          >
                            Revoke
                          </Button>
                        </WithConfirm>
                      </HorizontalGroup>
                    </InlineField>
                  </WithPermissionControlTooltip>
                </>
              )}
            </>
          ) : (
            <WithPermissionControlTooltip userAction={UserActions.UserSettingsWrite}>
              <InlineField
                label="iCal link"
                labelWidth={12}
                tooltip={'Secret iCal export link to add your assigned on call shifts to your calendar'}
              >
                <Button onClick={handleCreateiCalLink} variant="secondary" data-testid="create-ical-link">
                  Create
                </Button>
              </InlineField>
            </WithPermissionControlTooltip>
          )}
        </>
      )}
      <Alert title="Note: We do not have control over when a client refreshes an imported calendar." severity="info" />
    </>
  );
};
