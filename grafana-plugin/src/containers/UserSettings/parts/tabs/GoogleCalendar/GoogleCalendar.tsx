import React, { useEffect, useState } from 'react';

import { css } from '@emotion/css';
import { Button, HorizontalGroup, Switch, VerticalGroup, useStyles2 } from '@grafana/ui';
import { observer } from 'mobx-react';

import { Block } from 'components/GBlock/Block';
import { Text } from 'components/Text/Text';
import { WithConfirm } from 'components/WithConfirm/WithConfirm';
import { GSelect } from 'containers/GSelect/GSelect';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import GoogleCalendarLogo from 'icons/GoogleCalendarLogo';
import { Schedule } from 'models/schedule/schedule.types';
import { UserHelper } from 'models/user/user.helpers';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization/authorization';

const GoogleCalendar: React.FC<{ id: ApiSchemas['User']['pk'] }> = observer(({ id }) => {
  const { userStore, scheduleStore } = useStore();

  const styles = useStyles2(getStyles);

  const [googleCalendarSettings, setGoogleCalendarSettings] =
    useState<ApiSchemas['User']['google_calendar_settings']>();
  const [showSchedulesDropdown, setShowSchedulesDropdown] = useState<boolean>();

  useEffect(() => {
    (async () => {
      const user = await userStore.fetchItemById({ userPk: id });
      setGoogleCalendarSettings(user.google_calendar_settings);
      setShowSchedulesDropdown(user.google_calendar_settings.oncall_schedules_to_consider_for_shift_swaps?.length > 0);
    })();
  }, []);

  const handleShowSchedulesDropdownChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.checked;
    setShowSchedulesDropdown(value);

    if (!value) {
      handleSchedulesChange([]);
    }
  };

  const handleSchedulesChange = (value) => {
    setGoogleCalendarSettings((v) => ({ ...v, oncall_schedules_to_consider_for_shift_swaps: value }));

    userStore.updateCurrentUser({
      google_calendar_settings: { ...googleCalendarSettings, oncall_schedules_to_consider_for_shift_swaps: value },
    });
  };

  const user = userStore.items[id];

  return (
    <VerticalGroup>
      <Block bordered className={styles.root}>
        <VerticalGroup spacing="lg">
          {user.has_google_oauth2_connected ? (
            <VerticalGroup>
              <HorizontalGroup justify="space-between">
                <HorizontalGroup>
                  <GoogleCalendarLogo width={32} height={32} />
                  <Text>Google calendar is connected</Text>
                </HorizontalGroup>
                <WithPermissionControlTooltip userAction={UserActions.UserSettingsWrite}>
                  <WithConfirm title="Are you sure to disconnect your Google account?" confirmText="Disconnect">
                    <Button variant="destructive" onClick={userStore.disconnectGoogle}>
                      Disconnect
                    </Button>
                  </WithConfirm>
                </WithPermissionControlTooltip>
              </HorizontalGroup>
            </VerticalGroup>
          ) : (
            <HorizontalGroup justify="space-between" spacing="lg">
              <HorizontalGroup spacing="md">
                <GoogleCalendarLogo width={32} height={32} />
                <div>
                  <Text.Title level={5}>Connect your Google Calendar</Text.Title>
                  <Text type="secondary">
                    This connection allows Grafana OnCall to read your Out of Office events and autogenerate Shift Swap
                    Requests
                  </Text>
                </div>
              </HorizontalGroup>
              <WithPermissionControlTooltip userAction={UserActions.UserSettingsWrite}>
                <Button variant="primary" onClick={UserHelper.handleConnectGoogle}>
                  Connect
                </Button>
              </WithPermissionControlTooltip>
            </HorizontalGroup>
          )}

          {user.has_google_oauth2_connected && (
            <VerticalGroup>
              <WithPermissionControlTooltip userAction={UserActions.UserSettingsWrite}>
                <HorizontalGroup align="center">
                  <Switch value={showSchedulesDropdown} onChange={handleShowSchedulesDropdownChange} />
                  <Text type="secondary">Specify the schedules to sync with Google calendar</Text>
                </HorizontalGroup>
              </WithPermissionControlTooltip>
              {showSchedulesDropdown && (
                <div style={{ width: '100%' }}>
                  <WithPermissionControlTooltip userAction={UserActions.UserSettingsWrite}>
                    <GSelect<Schedule>
                      isMulti
                      showSearch
                      allowClear
                      disabled={false}
                      items={scheduleStore.items}
                      fetchItemsFn={scheduleStore.updateItems}
                      fetchItemFn={scheduleStore.updateItem}
                      getSearchResult={scheduleStore.getSearchResult}
                      displayField="name"
                      valueField="id"
                      placeholder="Select Schedules"
                      value={googleCalendarSettings?.oncall_schedules_to_consider_for_shift_swaps}
                      onChange={handleSchedulesChange}
                    />
                  </WithPermissionControlTooltip>
                </div>
              )}
            </VerticalGroup>
          )}
        </VerticalGroup>
      </Block>
    </VerticalGroup>
  );
});

export const getStyles = () => ({
  root: css({
    width: '100%',
  }),
});

export { GoogleCalendar };
