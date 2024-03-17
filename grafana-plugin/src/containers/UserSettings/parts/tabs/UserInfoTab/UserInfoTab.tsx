import React, { useCallback } from 'react';

import { Button, HorizontalGroup, Icon, InlineField, Input, Legend } from '@grafana/ui';
import cn from 'classnames/bind';

import { GrafanaTeamSelect } from 'containers/GrafanaTeamSelect/GrafanaTeamSelect';
import { UserSettingsTab } from 'containers/UserSettings/UserSettings.types';
import { Connectors } from 'containers/UserSettings/parts/connectors/Connectors';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useStore } from 'state/useStore';

import styles from './UserInfoTab.module.css';
import { makeRequest } from 'network/network';
import { AppFeature } from 'state/features';

const cx = cn.bind(styles);

interface UserInfoTabProps {
  id: ApiSchemas['User']['pk'];
  onTabChange: (tab: UserSettingsTab) => void;
}

export const UserInfoTab = (props: UserInfoTabProps) => {
  const { id } = props;

  const store = useStore();
  const { userStore } = store;

  const storeUser = userStore.items[id];
  let width = 15;

  const handleOpenGoogleInstructions = useCallback(async () => {
    /**
     * TODO: should this be moved to a "store" class?
     */
    const url_for_redirect = await makeRequest('/login/google-oauth2/', {});
    window.location = url_for_redirect;
  }, []);

  const ConnectGoogle = () => {
    if (!store.hasFeature(AppFeature.GoogleOauth2)) {
      return null;
    } else if (storeUser.has_google_oauth2_connected) {
      // TODO: style this
      return <p>Google already connected</p>;
    }
    // TODO: style this
    return (
      <Button onClick={handleOpenGoogleInstructions}>
        <HorizontalGroup spacing="xs" align="center">
          <Icon name="external-link-alt" className={cx('external-link-style')} /> Open Google connection page
        </HorizontalGroup>
      </Button>
    );
  };

  return (
    <>
      <Legend>User information</Legend>
      <InlineField
        label="Username"
        labelWidth={width}
        grow
        disabled
        tooltip="To edit username go to Grafana user management"
      >
        <Input value={storeUser.username || ''} />
      </InlineField>
      <InlineField label="Email" labelWidth={width} grow disabled tooltip="To edit email go to Grafana user management">
        <Input value={storeUser.email || ''} />
      </InlineField>
      <InlineField label="Timezone" labelWidth={width} grow disabled>
        <Input value={storeUser.timezone || ''} />
      </InlineField>
      <InlineField
        label="Default Team"
        labelWidth={width}
        grow
        tooltip="Default team will be pre-selected when you create new resources, such as integrations, schedules, etc."
      >
        <GrafanaTeamSelect
          withoutModal
          defaultValue={storeUser.current_team}
          onSelect={async (value) => {
            await userStore.updateUser({ pk: storeUser.pk, current_team: value });
            store.grafanaTeamStore.updateItems();
          }}
        />
      </InlineField>
      <Legend>Notification channels</Legend>
      <Connectors {...props} />
      <ConnectGoogle />
    </>
  );
};
