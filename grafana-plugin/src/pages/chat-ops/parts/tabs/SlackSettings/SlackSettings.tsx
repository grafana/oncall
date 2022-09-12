import React, { Component } from 'react';

import { Field, HorizontalGroup, LoadingPlaceholder, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import Tutorial from 'components/Tutorial/Tutorial';
import { TutorialStep } from 'components/Tutorial/Tutorial.types';
import GSelect from 'containers/GSelect/GSelect';
import RemoteSelect from 'containers/RemoteSelect/RemoteSelect';
import SlackIntegrationButton from 'containers/SlackIntegrationButton/SlackIntegrationButton';
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

interface SlackState {}

@observer
class SlackSettings extends Component<SlackProps, SlackState> {
  state: SlackState = {};

  componentDidMount() {
    this.update();
  }

  update = () => {
    const { store } = this.props;

    store.slackChannelStore.updateItems();
    store.slackStore.updateSlackSettings();
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
        <Text.Title level={4} className={cx('title')}>
          Slack
        </Text.Title>
        <div className={cx('slack-settings')}>
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
        </div>
        <div className={cx('slack-settings')}>
          <Text.Title level={4} className={cx('title')}>
            Additional settings
          </Text.Title>
          <Field
            label="Timeout for acknowledged alerts"
            description="Set up a reminder and timeout for acknowledged alert to never forget about them"
          >
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
        <Text.Title level={4} className={cx('title')}>
          Remove integration
        </Text.Title>
        <SlackIntegrationButton className={cx('slack-button')} />
      </div>
    );
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

    return (
      <Tutorial
        step={TutorialStep.Slack}
        title={
          <VerticalGroup align="center" spacing="lg">
            <Text.Title level={2}>Connect your Slack workspace</Text.Title>
            <Text>
              Bring the whole incident lifecycle to Slack, from alerts, monitoring, escalations to resolution notes and
              reports.
            </Text>

            <SlackIntegrationButton className={cx('slack-button')} />

            {store.hasFeature(AppFeature.LiveSettings) && (
              <Text type="secondary">
                Before installing <PluginLink query={{ page: 'live-settings' }}>check ENV variables</PluginLink> related
                to Slack please
              </Text>
            )}
          </VerticalGroup>
        }
      />
    );
  };
}

export default withMobXProviderContext(SlackSettings);
