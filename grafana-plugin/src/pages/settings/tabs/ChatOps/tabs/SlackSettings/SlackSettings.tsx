import React, { Component } from 'react';

import { Alert, Field, HorizontalGroup, LoadingPlaceholder, VerticalGroup, Icon, Button } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import Block from 'components/GBlock/Block';
import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import GSelect from 'containers/GSelect/GSelect';
import RemoteSelect from 'containers/RemoteSelect/RemoteSelect';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { SlackNewIcon } from 'icons';
import { PRIVATE_CHANNEL_NAME } from 'models/slack_channel/slack_channel.config';
import { SlackChannel } from 'models/slack_channel/slack_channel.types';
import { AppFeature } from 'state/features';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import { showApiError } from 'utils';
import { UserActions } from 'utils/authorization';
import { DOCS_SLACK_SETUP } from 'utils/consts';

import styles from './SlackSettings.module.css';

const cx = cn.bind(styles);

interface SlackProps extends WithStoreProps {}

interface SlackState {
  showENVVariablesButton: boolean;
}

@observer
class SlackSettings extends Component<SlackProps, SlackState> {
  state: SlackState = {
    showENVVariablesButton: false,
  };

  componentDidMount() {
    const { store } = this.props;
    if (store.hasFeature(AppFeature.LiveSettings)) {
      this.getSlackLiveSettings().then(() => {
        this.update();
      });
    } else {
      this.update();
    }
  }

  handleOpenSlackInstructions = () => {
    const { store } = this.props;
    store.slackStore.installSlackIntegration().catch(showApiError);
  };

  update = () => {
    const { store } = this.props;

    store.slackChannelStore.updateItems();
    store.slackStore.updateSlackSettings();
  };

  getSlackLiveSettings = async () => {
    const { store } = this.props;
    const results = await store.globalSettingStore.getAll();

    const slackClientOAUTH = results.find((element: { name: string }) => element.name === 'SLACK_CLIENT_OAUTH_ID');
    const slackClientOAUTHSecret = results.find(
      (element: { name: string }) => element.name === 'SLACK_CLIENT_OAUTH_SECRET'
    );
    const slackRedirectHost = results.find((element: { name: string }) => element.name === 'SLACK_CLIENT_OAUTH_ID');
    const slackSigningSecret = results.find((element: { name: string }) => element.name === 'SLACK_SIGNING_SECRET');

    if (
      slackClientOAUTH?.error ||
      slackClientOAUTHSecret?.error ||
      slackRedirectHost?.error ||
      slackSigningSecret?.error
    ) {
      this.setState({ showENVVariablesButton: true });
    }
  };

  render() {
    const { store } = this.props;
    const { teamStore } = store;

    if (!teamStore.currentTeam) {
      return <LoadingPlaceholder text="Loading..." />;
    }

    return teamStore.currentTeam?.slack_team_identity ? this.renderSlackIntegration() : this.renderSlackStub();
  }

  renderSlackIntegration = () => {
    const { store } = this.props;
    const { teamStore, slackStore } = store;

    return (
      <div className={cx('root')}>
        <div className={cx('title')}>
          <Text.Title level={3}>Slack</Text.Title>
        </div>
        <div className={cx('slack-settings')}>
          <HorizontalGroup justify="space-between">
            <HorizontalGroup align="center">
              <Field label="Slack Workspace">
                <div className={cx('select', 'control', 'team_workspace')}>
                  <Text>{store.teamStore.currentTeam.slack_team_identity?.cached_name}</Text>
                </div>
              </Field>
              <Field label="Default channel for Slack notifications">
                <WithPermissionControlTooltip userAction={UserActions.ChatOpsUpdateSettings}>
                  <GSelect
                    showSearch
                    className={cx('select', 'control')}
                    modelName="slackChannelStore"
                    displayField="display_name"
                    valueField="id"
                    placeholder="Select Slack Channel"
                    value={teamStore.currentTeam?.slack_channel?.id}
                    onChange={this.handleSlackChannelChange}
                    nullItemName={PRIVATE_CHANNEL_NAME}
                  />
                </WithPermissionControlTooltip>
              </Field>
            </HorizontalGroup>
            <WithPermissionControlTooltip userAction={UserActions.ChatOpsUpdateSettings}>
              <WithConfirm
                title="Remove Slack Integration for all of OnCall"
                description={
                  <Alert severity="error" title="WARNING">
                    <p>Are you sure to delete this Slack Integration?</p>
                    <p>
                      Removing the integration will also irreverisbly remove the following data for your OnCall plugin:
                    </p>
                    <ul style={{ marginLeft: '20px' }}>
                      <li>default organization Slack channel</li>
                      <li>default Slack channels for OnCall Integrations</li>
                      <li>Slack channels & Slack user groups for OnCall Schedules</li>
                      <li>linked Slack usernames for OnCall Users</li>
                    </ul>
                    <br />
                    <p>
                      If you would like to instead remove your linked Slack username, please head{' '}
                      <PluginLink query={{ page: 'users/me' }}>here</PluginLink>.
                    </p>
                  </Alert>
                }
                confirmationText="DELETE"
              >
                <Button variant="destructive" size="sm" onClick={() => this.removeSlackIntegration()}>
                  Disconnect
                </Button>
              </WithConfirm>
            </WithPermissionControlTooltip>
          </HorizontalGroup>
        </div>
        <div className={cx('slack-settings')}>
          <Text.Title level={5} className={cx('title')}>
            Additional settings
          </Text.Title>
          <Field label="Timeout for acknowledged alerts">
            <HorizontalGroup>
              <WithPermissionControlTooltip userAction={UserActions.ChatOpsWrite}>
                <RemoteSelect
                  className={cx('select')}
                  showSearch={false}
                  href={'/slack_settings/acknowledge_remind_options/'}
                  value={slackStore.slackSettings?.acknowledge_remind_timeout}
                  onChange={this.getSlackSettingsChangeHandler('acknowledge_remind_timeout')}
                />
              </WithPermissionControlTooltip>
              <WithPermissionControlTooltip userAction={UserActions.ChatOpsWrite}>
                <RemoteSelect
                  className={cx('select')}
                  disabled={slackStore.slackSettings?.acknowledge_remind_timeout === 0}
                  showSearch={false}
                  href={'/slack_settings/unacknowledge_timeout_options/'}
                  value={slackStore.slackSettings?.unacknowledge_timeout}
                  onChange={this.getSlackSettingsChangeHandler('unacknowledge_timeout')}
                />
              </WithPermissionControlTooltip>
            </HorizontalGroup>
          </Field>
        </div>
      </div>
    );
  };

  renderSlackWorkspace = () => {
    const { store } = this.props;
    return <Text>{store.teamStore.currentTeam.slack_team_identity?.cached_name}</Text>;
  };

  renderSlackChannels = () => {
    const { store } = this.props;
    return (
      <WithPermissionControlTooltip userAction={UserActions.ChatOpsUpdateSettings}>
        <GSelect
          showSearch
          className={cx('select', 'control')}
          modelName="slackChannelStore"
          displayField="display_name"
          valueField="id"
          placeholder="Select Slack Channel"
          value={store.teamStore.currentTeam?.slack_channel?.id}
          onChange={this.handleSlackChannelChange}
          nullItemName={PRIVATE_CHANNEL_NAME}
        />
      </WithPermissionControlTooltip>
    );
  };

  removeSlackIntegration = () => {
    const { store } = this.props;
    store.slackStore
      .removeSlackIntegration()
      .then(() => {
        store.teamStore.loadCurrentTeam();
      })
      .catch(showApiError);
  };

  getSlackSettingsChangeHandler = (field: string) => {
    const { store } = this.props;
    const { slackStore } = store;

    return (value: number | boolean) => {
      slackStore.saveSlackSettings({ [field]: value });
    };
  };

  handleSlackChannelChange = async (value: SlackChannel['id']) => {
    const { store } = this.props;
    const { slackStore } = store;

    await slackStore.setGeneralLogChannelId(value);

    store.teamStore.loadCurrentTeam();
  };

  renderSlackStub = () => {
    const { store } = this.props;
    const { showENVVariablesButton } = this.state;
    const isLiveSettingAvailable = store.hasFeature(AppFeature.LiveSettings) && showENVVariablesButton;

    return (
      <VerticalGroup spacing="lg">
        <Text.Title level={2}>Connect Slack workspace</Text.Title>
        <Block bordered withBackground className={cx('slack-infoblock')}>
          <VerticalGroup align="center">
            <div className={cx('infoblock-icon')}>
              <SlackNewIcon />
            </div>
            <Text className={cx('infoblock-text')}>
              Slack connection will allow you to manage alert groups in your team Slack workspace.
            </Text>
            <Text className={cx('infoblock-text')}>
              After a basic workspace connection your team members need to connect their personal Slack accounts in
              order to be allowed to manage alert groups.
            </Text>
            {isLiveSettingAvailable && (
              <Text type="secondary" className={cx('infoblock-text')}>
                For bot creating instructions and additional information please read{' '}
                <a href={DOCS_SLACK_SETUP} target="_blank" rel="noreferrer">
                  <Text type="link">our documentation</Text>
                </a>
              </Text>
            )}

            <img
              style={{ height: '350px', display: 'block', margin: '0 auto' }}
              src="public/plugins/grafana-oncall-app/img/slack_instructions.png"
            />
          </VerticalGroup>
        </Block>
        {isLiveSettingAvailable ? (
          <PluginLink query={{ page: 'live-settings' }}>
            <Button variant="primary">Setup ENV Variables</Button>
          </PluginLink>
        ) : (
          <HorizontalGroup>
            <Button onClick={this.handleOpenSlackInstructions}>
              <Icon name="external-link-alt" className={cx('external-link-style')} /> Open Slack connection page
            </Button>
            {store.hasFeature(AppFeature.LiveSettings) && (
              <PluginLink query={{ page: 'live-settings' }}>
                <Button variant="secondary">See ENV Variables</Button>
              </PluginLink>
            )}
          </HorizontalGroup>
        )}
      </VerticalGroup>
    );
  };
}

export default withMobXProviderContext(SlackSettings);
