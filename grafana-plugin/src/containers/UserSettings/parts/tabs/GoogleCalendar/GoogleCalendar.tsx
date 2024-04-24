import React, { useEffect, useState } from 'react';

import { css } from '@emotion/css';
import { Button, HorizontalGroup, Switch, VerticalGroup, useStyles2 } from '@grafana/ui';
import { observer } from 'mobx-react';
import { getUtilStyles } from 'styles/utils.styles';

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
import { DOCS_ROOT } from 'utils/consts';

const GoogleCalendar: React.FC<{ id: ApiSchemas['User']['pk'] }> = observer(({ id }) => {
  const { userStore, scheduleStore } = useStore();

  const utils = useStyles2(getUtilStyles);

  const [showSchedulesDropdown, setShowSchedulesDropdown] = useState<boolean>();

  const user = userStore.items[id];

  useEffect(() => {
    setShowSchedulesDropdown(user.google_calendar_settings?.oncall_schedules_to_consider_for_shift_swaps?.length > 0);
  }, [user]);

  const handleShowSchedulesDropdownChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.checked;
    setShowSchedulesDropdown(value);

    if (!value) {
      handleSchedulesChange([]);
    }
  };

  const handleSchedulesChange = (value) => {
    userStore.updateUser({
      pk: id,
      google_calendar_settings: {
        ...user.google_calendar_settings,
        oncall_schedules_to_consider_for_shift_swaps: value,
      },
    });
  };

  return (
    <Block bordered className={utils.width100}>
      <VerticalGroup spacing="lg">
        {user.has_google_oauth2_connected ? (
          <VerticalGroup>
            <HorizontalGroup justify="space-between" spacing="lg" align="flex-start">
              <Heading connected />
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
          <HorizontalGroup justify="space-between" spacing="lg" align="flex-start">
            <Heading connected={false} />
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
              <HorizontalGroup spacing="md" align="center">
                <Switch value={showSchedulesDropdown} onChange={handleShowSchedulesDropdownChange} />
                <Text type="secondary">Specify the schedules to sync with Google calendar</Text>
              </HorizontalGroup>
            </WithPermissionControlTooltip>
            {showSchedulesDropdown && (
              <div className={utils.width100}>
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
                    value={user.google_calendar_settings.oncall_schedules_to_consider_for_shift_swaps}
                    onChange={handleSchedulesChange}
                  />
                </WithPermissionControlTooltip>
              </div>
            )}
          </VerticalGroup>
        )}
      </VerticalGroup>
    </Block>
  );
});

export const getStyles = () => ({
  icon: css({
    marginTop: '6px',
  }),
});

const Heading: React.FC<{ connected: boolean }> = ({ connected }) => {
  const styles = useStyles2(getStyles);

  return (
    <HorizontalGroup spacing="md" align="flex-start">
      <div className={styles.icon}>
        <GoogleCalendarLogo width={32} height={32} />
      </div>
      <VerticalGroup spacing="md">
        <VerticalGroup spacing="none">
          <Text.Title level={5}>
            {connected ? 'Google calendar is connected' : 'Connect your Google Calendar'}
          </Text.Title>
          {connected ? (
            <Text type="secondary">
              Add <Text type="primary">#grafana-oncall-ignore</Text> to an Out of Office event title to exclude it from
              Shift Swap Request creation.{' '}
              <a
                href={`${DOCS_ROOT}/manage/on-call-schedules/shift-swaps/#google-calendar-integration`}
                target="_blank"
                rel="noreferrer"
              >
                <Text type="link">Read more</Text>
              </a>
            </Text>
          ) : (
            <Text type="secondary">
              This connection allows OnCall to read your Out of Office events and autogenerate Shift Swap Requests.{' '}
              <a
                href={`${DOCS_ROOT}/manage/on-call-schedules/shift-swaps/#google-calendar-integration`}
                target="_blank"
                rel="noreferrer"
              >
                <Text type="link">Read more</Text>
              </a>
            </Text>
          )}
        </VerticalGroup>
        {!connected && (
          <Text type="secondary">
            Grafana OnCall's use and transfer to any other app of information received from Google APIs will adhere
            <br />
            to{' '}
            <a
              target="_blank"
              rel="noreferrer"
              href="https://developers.google.com/terms/api-services-user-data-policy#additional_requirements_for_specific_api_scopes"
            >
              <Text type="secondary" underline>
                Google API Services User Data Policy
              </Text>
            </a>
            , including the Limited Use requirements.
          </Text>
        )}
      </VerticalGroup>
    </HorizontalGroup>
  );
};

export { GoogleCalendar };
