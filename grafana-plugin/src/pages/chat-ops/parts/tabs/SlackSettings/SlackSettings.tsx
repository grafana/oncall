import React, { Component } from 'react';

import { Field, HorizontalGroup, LoadingPlaceholder, VerticalGroup, Icon, Button } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import { SlackNewIcon } from 'icons';
import Block from 'components/GBlock/Block';
import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import GSelect from 'containers/GSelect/GSelect';
import RemoteSelect from 'containers/RemoteSelect/RemoteSelect';
import { WithPermissionControl } from 'containers/WithPermissionControl/WithPermissionControl';
import { PRIVATE_CHANNEL_NAME } from 'models/slack_channel/slack_channel.config';
import { SlackChannel } from 'models/slack_channel/slack_channel.types';
import { AppFeature } from 'state/features';
import { WithStoreProps } from 'state/types';
import { UserAction } from 'state/userAction';
import { withMobXProviderContext } from 'state/withStore';

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
    this.getSlackLiveSettings();
    this.update();
  }

  handleOpenSlackInstructions = () => {
    const { store } = this.props;
    store.slackStore.installSlackIntegration();
  };

  update = () => {
    const { store } = this.props;

    store.slackChannelStore.updateItems();
    store.slackStore.updateSlackSettings();
  };

  getSlackLiveSettings = async () => {
    const { store } = this.props;
    const slackClientOAUTH = await store.globalSettingStore.getGlobalSettingItemByName('SLACK_CLIENT_OAUTH_ID');
    const slackClientOAUTHSecret = await store.globalSettingStore.getGlobalSettingItemByName(
      'SLACK_CLIENT_OAUTH_SECRET'
    );
    const slackRedirectHost = await store.globalSettingStore.getGlobalSettingItemByName(
      'SLACK_INSTALL_RETURN_REDIRECT_HOST'
    );
    const slackSigningSecret = await store.globalSettingStore.getGlobalSettingItemByName('SLACK_SIGNING_SECRET');

    console.log('slackClientOAUTH', slackClientOAUTH?.error);
    console.log('slackClientOAUTHSecret', slackClientOAUTHSecret?.error);
    console.log('slackRedirectHost', slackRedirectHost?.error);
    console.log('slackSigningSecret', slackSigningSecret?.error);
    if (
      slackClientOAUTH?.error ||
      slackClientOAUTHSecret?.error ||
      slackRedirectHost?.error ||
      slackSigningSecret?.error
    ) {
      console.log('BLA BLA');
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
                <WithPermissionControl userAction={UserAction.UpdateGeneralLogChannelId}>
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
                </WithPermissionControl>
              </Field>
            </HorizontalGroup>
            <WithPermissionControl userAction={UserAction.UpdateIntegrations}>
              <WithConfirm title="Are you sure to delete this Slack Integration?">
                <Button variant="destructive" size="sm" onClick={() => this.removeSlackIntegration()}>
                  Disconnect
                </Button>
              </WithConfirm>
            </WithPermissionControl>
          </HorizontalGroup>
        </div>
        <div className={cx('slack-settings')}>
          <Text.Title level={5} className={cx('title')}>
            Additional settings
          </Text.Title>
          <Field label="Timeout for acknowledged alerts">
            <HorizontalGroup>
              <WithPermissionControl userAction={UserAction.UpdateGeneralLogChannelId}>
                <RemoteSelect
                  className={cx('select')}
                  showSearch={false}
                  href={'/slack_settings/acknowledge_remind_options/'}
                  value={slackStore.slackSettings?.acknowledge_remind_timeout}
                  onChange={this.getSlackSettingsChangeHandler('acknowledge_remind_timeout')}
                />
              </WithPermissionControl>
              <WithPermissionControl userAction={UserAction.UpdateGeneralLogChannelId}>
                <RemoteSelect
                  className={cx('select')}
                  disabled={slackStore.slackSettings?.acknowledge_remind_timeout === 0}
                  showSearch={false}
                  href={'/slack_settings/unacknowledge_timeout_options/'}
                  value={slackStore.slackSettings?.unacknowledge_timeout}
                  onChange={this.getSlackSettingsChangeHandler('unacknowledge_timeout')}
                />
              </WithPermissionControl>
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
      <WithPermissionControl userAction={UserAction.UpdateGeneralLogChannelId}>
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
      </WithPermissionControl>
    );
  };

  renderActionButtons = () => {
    <WithPermissionControl userAction={UserAction.UpdateIntegrations}>
      <WithConfirm title="Are you sure to delete this Slack Integration?">
        <Button variant="destructive" size="sm" onClick={() => this.removeSlackIntegration()}>
          Disconnect
        </Button>
      </WithConfirm>
    </WithPermissionControl>;
  };

  removeSlackIntegration = () => {
    const { store } = this.props;
    store.slackStore.removeSlackIntegration().then(() => {
      store.teamStore.loadCurrentTeam();
    });
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
          <VerticalGroup align="center" spacing="lg">
            <SlackNewIcon />
            <Text>
              Slack connection will allow you to manage incidents in your team Slack workspace.
              <br />
              After a basic workspace connection, your team members need to connect their personal Slack accounts in
              order to be allowed to manage incidents.
            </Text>
            {isLiveSettingAvailable && (
              <Text type="secondary">
                For bot creating instructions and additional information please read{' '}
                <a href="https://grafana.com/docs/grafana-cloud/oncall/open-source/#slack-setup">
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
            <PluginLink query={{ page: 'live-settings' }}>
              <Button variant="secondary">See ENV Variables</Button>
            </PluginLink>
          </HorizontalGroup>
        )}
      </VerticalGroup>
    );
  };
}

export default withMobXProviderContext(SlackSettings);
