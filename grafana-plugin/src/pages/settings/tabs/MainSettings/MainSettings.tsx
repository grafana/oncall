import React from 'react';

import { Field, Input, Switch } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import LegacyNavHeading from 'navbar/LegacyNavHeading';

import Text from 'components/Text/Text';
import ApiTokenSettings from 'containers/ApiTokenSettings/ApiTokenSettings';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import TeamsSettings from 'pages/settings/tabs/TeamsSettings/TeamsSettings';
import { isTopNavbar } from 'plugin/GrafanaPluginRootPage.helpers';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import { UserActions } from 'utils/authorization';

import styles from './MainSettings.module.css';

const cx = cn.bind(styles);

interface SettingsPageProps extends WithStoreProps {}

interface SettingsPageState {
  apiUrl?: string;
}

@observer
class SettingsPage extends React.Component<SettingsPageProps, SettingsPageState> {
  state: SettingsPageState = {
    apiUrl: '',
  };

  async componentDidMount() {
    const { store } = this.props;
    const url = await store.getApiUrlForSettings();
    this.setState({ apiUrl: url });
  }

  render() {
    const { organizationStore } = this.props.store;
    const { currentOrganization } = organizationStore;
    const { apiUrl } = this.state;

    return (
      <div className={cx('root')}>
        <LegacyNavHeading>
          <Text.Title level={3} className={cx('title')}>
            Organization settings
          </Text.Title>
        </LegacyNavHeading>

        <div className={cx('settings')}>
          <Text.Title level={3} className={cx('title')}>
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
                  organizationStore.saveCurrentOrganization({
                    is_resolution_note_required: event.currentTarget.checked,
                  });
                }}
              />
            </WithPermissionControlTooltip>
          </Field>
        </div>
        {!isTopNavbar() && (
          <div style={{ marginBottom: '20px' }}>
            <Text.Title level={3} className={cx('title')}>
              Teams and Access Settings
            </Text.Title>
            <TeamsSettings />
          </div>
        )}
        <Text.Title level={3} className={cx('title')}>
          API URL
        </Text.Title>
        <div>
          <Field>
            <Input value={apiUrl} disabled />
          </Field>
        </div>
        <ApiTokenSettings />
      </div>
    );
  }
}

export default withMobXProviderContext(SettingsPage);
