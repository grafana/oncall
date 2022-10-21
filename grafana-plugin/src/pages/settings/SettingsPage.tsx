import React from 'react';

import { Field, Input, Switch } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import Text from 'components/Text/Text';
import ApiTokenSettings from 'containers/ApiTokenSettings/ApiTokenSettings';
import { WithPermissionControl } from 'containers/WithPermissionControl/WithPermissionControl';
import { WithStoreProps } from 'state/types';
import { UserAction } from 'state/userAction';
import { withMobXProviderContext } from 'state/withStore';

import styles from './SettingsPage.module.css';

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
      <div className={cx('root')}>
        <Text.Title level={3} className={cx('title')}>
          Organization settings
        </Text.Title>
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
    );
  }
}

export default withMobXProviderContext(SettingsPage);
