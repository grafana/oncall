import React from 'react';

import { css } from '@emotion/css';
import { Field, Input, Switch, useStyles2 } from '@grafana/ui';
import { observer } from 'mobx-react';
import { LegacyNavHeading } from 'navbar/LegacyNavHeading';

import { Text } from 'components/Text/Text';
import { ApiTokenSettings } from 'containers/ApiTokenSettings/ApiTokenSettings';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { TeamsSettings } from 'pages/settings/tabs/TeamsSettings/TeamsSettings';
import { isTopNavbar } from 'plugin/GrafanaPluginRootPage.helpers';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization/authorization';

export const MainSettings = observer(() => {
  const styles = useStyles2(getStyles);
  const {
    organizationStore: { currentOrganization, saveCurrentOrganization },
    pluginStore: { apiUrlFromStatus },
  } = useStore();

  return (
    <div>
      <LegacyNavHeading>
        <Text.Title level={3} className={styles.title}>
          Organization settings
        </Text.Title>
      </LegacyNavHeading>

      <div className={styles.settings}>
        <Text.Title level={3} className={styles.title}>
          Resolution Note
        </Text.Title>
        <Field
          loading={!currentOrganization}
          label="Require a resolution note when resolving Alert Groups"
          description={`Once user clicks "Resolve" for an Alert Group, they will be required to fill in a resolution note about the Alert Group`}
        >
          <WithPermissionControlTooltip userAction={UserActions.OtherSettingsWrite}>
            <Switch
              value={currentOrganization?.is_resolution_note_required}
              onChange={(event) => {
                saveCurrentOrganization({
                  is_resolution_note_required: event.currentTarget.checked,
                });
              }}
            />
          </WithPermissionControlTooltip>
        </Field>
      </div>
      {!isTopNavbar() && (
        <div style={{ marginBottom: '20px' }}>
          <Text.Title level={3} className={styles.title}>
            Teams and Access Settings
          </Text.Title>
          <TeamsSettings />
        </div>
      )}
      <Text.Title level={3} className={styles.title}>
        API URL
      </Text.Title>
      <div>
        <Field>
          <Input value={apiUrlFromStatus} disabled />
        </Field>
      </div>
      <ApiTokenSettings />
    </div>
  );
});

const getStyles = () => ({
  settings: css`
    width: fit-content;
  `,
  title: css`
    margin-bottom: 20px;
  `,
});
