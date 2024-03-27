import React, { useEffect, useState } from 'react';

import { Button, Divider, HorizontalGroup, InlineSwitch, VerticalGroup } from '@grafana/ui';
import { observer } from 'mobx-react';

import { Block } from 'components/GBlock/Block';
import { Text } from 'components/Text/Text';
import { WithConfirm } from 'components/WithConfirm/WithConfirm';
import { GSelect } from 'containers/GSelect/GSelect';
import GoogleLogo from 'icons/GoogleLogo';
import { Schedule } from 'models/schedule/schedule.types';
import { UserHelper } from 'models/user/user.helpers';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useStore } from 'state/useStore';

const GoogleCalendar: React.FC<{ id: ApiSchemas['User']['pk'] }> = observer(({ id }) => {
  const { userStore, scheduleStore } = useStore();

  const user = userStore.items[id];
  const [googleCalendarSettings, setGoogleCalendarSettings] = useState(user?.google_calendar_settings);
  const [showSchedulesDropdown, setShowSchedulesDropdown] = useState(
    user.google_calendar_settings?.specific_oncall_schedules_to_sync.length > 0
  );

  const handleShowSchedulesDropdownChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.checked;
    setShowSchedulesDropdown(value);

    if (!value) {
      handleSchedulesChange([]);
    }
  };

  useEffect(() => {
    if (user) {
      setGoogleCalendarSettings(user.google_calendar_settings);
    }
  }, [user]);

  const handleSchedulesChange = (value) => {
    setGoogleCalendarSettings((v) => ({ ...v, specific_oncall_schedules_to_sync: value }));

    userStore.updateCurrentUser({
      google_calendar_settings: { ...googleCalendarSettings, specific_oncall_schedules_to_sync: value },
    });
  };

  return (
    <VerticalGroup>
      <Block bordered style={{ width: '100%' }}>
        <VerticalGroup>
          <VerticalGroup spacing="none">
            <Text.Title level={5}>Google Calendar</Text.Title>
            <Text type="secondary">
              Connect personal calendar to sync PTOs and OOO events with your OnCall schedules.
            </Text>
          </VerticalGroup>
          {user.has_google_oauth2_connected ? (
            <VerticalGroup>
              <HorizontalGroup justify="space-between">
                <HorizontalGroup>
                  <GoogleLogo width={24} height={24} />
                  <Text>Google calendar is connected</Text>
                </HorizontalGroup>
                <WithConfirm title="Are you sure to disconnect your Google account?" confirmText="Disconnect">
                  <Button
                    variant="destructive"
                    onClick={() => {
                      userStore.disconnectGoogle();
                    }}
                  >
                    Disconnect
                  </Button>
                </WithConfirm>
              </HorizontalGroup>
            </VerticalGroup>
          ) : (
            <HorizontalGroup justify="space-between">
              <HorizontalGroup>
                <GoogleLogo width={32} height={32} />
                <Text>Connect using your Google account</Text>
              </HorizontalGroup>
              <Button variant="secondary" onClick={UserHelper.handleConnectGoogle}>
                Connect
              </Button>
            </HorizontalGroup>
          )}

          {user.has_google_oauth2_connected && (
            <VerticalGroup>
              <Divider />

              <InlineSwitch
                showLabel
                label="Specify the schedules to sync with Google calendar"
                value={showSchedulesDropdown}
                transparent
                onChange={handleShowSchedulesDropdownChange}
              />
              {showSchedulesDropdown && (
                <div style={{ width: '100%' }}>
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
                    value={googleCalendarSettings?.specific_oncall_schedules_to_sync}
                    onChange={handleSchedulesChange}
                  />
                </div>
              )}
            </VerticalGroup>
          )}
        </VerticalGroup>
      </Block>
    </VerticalGroup>
  );
});

export { GoogleCalendar };
