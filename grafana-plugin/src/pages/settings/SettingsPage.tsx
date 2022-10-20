import React from 'react';

import { DatePickerWithInput, Field, Input, Switch } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import moment from 'moment';

import Text from 'components/Text/Text';
import ApiTokenSettings from 'containers/ApiTokenSettings/ApiTokenSettings';
import GSelect from 'containers/GSelect/GSelect';
import { WithPermissionControl } from 'containers/WithPermissionControl/WithPermissionControl';
import { PRIVATE_CHANNEL_NAME } from 'models/slack_channel/slack_channel.config';
import { WithStoreProps } from 'state/types';
import { UserAction } from 'state/userAction';
import { withMobXProviderContext } from 'state/withStore';

import styles from './SettingsPage.module.css';
import PluginLink from 'components/PluginLink/PluginLink';
import { PluginPage } from 'PluginPage';
import { pages } from 'pages';
import { config } from '@grafana/runtime';

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
    const { store } = this.props;
    const { teamStore } = store;
    const { apiUrl } = this.state;

    return (
      <PluginPage pageNav={pages['settings'].getPageNav()}>
        <div className={cx('root', { navbarRootFallback: !config.featureToggles.topnav })}>
          <div className={cx('settings')}>
            <Field
              loading={!teamStore.currentTeam}
              label="Require resolution note when resolve incident"
              description="Once user clicks “Resolve” for an incident they are require to fill a resolution note about the incident"
            >
              <WithPermissionControl userAction={UserAction.UpdateGlobalSettings}>
                <Switch
                  value={teamStore.currentTeam?.is_resolution_note_required}
                  onChange={(event) => {
                    teamStore.saveCurrentTeam({
                      is_resolution_note_required: event.currentTarget.checked,
                    });
                  }}
                />
              </WithPermissionControl>
            </Field>
            {/*<Field
            loading={!teamStore.currentTeam}
            label="Archive alert created before given date"
            description="Alerts before and including this date will be resolved and archived"
          >
            <WithPermissionControl userAction={UserAction.UpdateGlobalSettings}>
              <DatePickerWithInput
                closeOnSelect
                width={40}
                value={
                  teamStore.currentTeam?.archive_alerts_from
                    ? moment(teamStore.currentTeam?.archive_alerts_from).toDate()
                    : undefined
                }
                onChange={(value) => {
                  teamStore.saveCurrentTeam({ archive_alerts_from: moment(value).format('YYYY-MM-DD') });
                }}
              />
            </WithPermissionControl>
          </Field>*/}
          </div>
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
      </PluginPage>
    );
  }
}

export default withMobXProviderContext(SettingsPage);
