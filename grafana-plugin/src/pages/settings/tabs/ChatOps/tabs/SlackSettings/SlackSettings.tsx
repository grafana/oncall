import React, { Component } from 'react';

import {
  Alert,
  HorizontalGroup,
  LoadingPlaceholder,
  VerticalGroup,
  Icon,
  Button,
  InlineField,
  Input,
  Legend,
} from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import { Block } from 'components/GBlock/Block';
import { PluginLink } from 'components/PluginLink/PluginLink';
import { Text } from 'components/Text/Text';
import { WithConfirm } from 'components/WithConfirm/WithConfirm';
import { GSelect } from 'containers/GSelect/GSelect';
import { RemoteSelect } from 'containers/RemoteSelect/RemoteSelect';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { SlackNewIcon } from 'icons/Icons';
import { PRIVATE_CHANNEL_NAME } from 'models/slack_channel/slack_channel.config';
import { SlackChannel } from 'models/slack_channel/slack_channel.types';
import { AppFeature } from 'state/features';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import { UserActions } from 'utils/authorization/authorization';
import { DOCS_SLACK_SETUP } from 'utils/consts';
import { showApiError } from 'utils/utils';

import styles from './SlackSettings.module.css';

const cx = cn.bind(styles);

interface SlackProps extends WithStoreProps {}

interface SlackState {
  showENVVariablesButton: boolean;
}

@observer
class _SlackSettings extends Component<SlackProps, SlackState> {
  state: SlackState = {
    showENVVariablesButton: false,
  };

  componentDidMount() {
    this.onDidMount();
  }

  onDidMount = async () => {
    const { store } = this.props;
    if (store.hasFeature(AppFeature.LiveSettings)) {
      await this.getSlackLiveSettings();
    }
    this.update();
  };

  handleOpenSlackInstructions = async () => {
    const { store } = this.props;
    try {
      await store.slackStore.installSlackIntegration();
    } catch (err) {
      showApiError(err);
    }
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
    const { currentOrganization } = this.props.store.organizationStore;

    if (!currentOrganization) {
      return <LoadingPlaceholder text="Loading..." />;
    }

    return currentOrganization?.slack_team_identity ? this.renderSlackIntegration() : this.renderSlackStub();
  }

  renderSlackIntegration = () => {
    const { store } = this.props;
    const {
      organizationStore: { currentOrganization },
      slackStore,
      slackChannelStore,
    } = store;

    return (
      <div className={cx('root')}>
        <Legend>Slack App settings</Legend>
        <InlineField label="Slack Workspace" grow disabled>
          <Input value={currentOrganization?.slack_team_identity?.cached_name} />
        </InlineField>
        <InlineField
          label="Default channel for Slack notifications"
          tooltip="The selected channel will be used as a fallback in the event that a schedule or integration does not have a configured channel"
        >
          <WithPermissionControlTooltip userAction={UserActions.ChatOpsUpdateSettings}>
            <GSelect<SlackChannel>
              items={slackChannelStore.items}
              fetchItemsFn={slackChannelStore.updateItems}
              fetchItemFn={slackChannelStore.updateItem}
              getSearchResult={slackChannelStore.getSearchResult}
              displayField="display_name"
              valueField="id"
              placeholder="Select Slack Channel"
              value={currentOrganization?.slack_channel?.id}
              onChange={this.handleSlackChannelChange}
              nullItemName={PRIVATE_CHANNEL_NAME}
            />
          </WithPermissionControlTooltip>
        </InlineField>
        <Alert
          severity="info"
          title="Tip: Create a separate channel for OnCall Slack App notifications (catch-all). Avoid using #general, etc."
        />
        <InlineField>
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
              <Button variant="destructive" onClick={() => this.removeSlackIntegration()}>
                Disconnect Slack App
              </Button>
            </WithConfirm>
          </WithPermissionControlTooltip>
        </InlineField>
        <Legend>Additional settings</Legend>
        <InlineField
          label="Timeout for acknowledged alerts"
          tooltip="Slack app will send reminders into alert group slack thread and unacknowledge alert group if no confirmation is received."
        >
          <HorizontalGroup spacing="xs">
            <WithPermissionControlTooltip userAction={UserActions.ChatOpsWrite}>
              <RemoteSelect
                showSearch={false}
                href={'/slack_settings/acknowledge_remind_options/'}
                value={slackStore.slackSettings?.acknowledge_remind_timeout}
                onChange={this.getSlackSettingsChangeHandler('acknowledge_remind_timeout')}
              />
            </WithPermissionControlTooltip>
            <WithPermissionControlTooltip userAction={UserActions.ChatOpsWrite}>
              <RemoteSelect
                disabled={slackStore.slackSettings?.acknowledge_remind_timeout === 0}
                showSearch={false}
                href={'/slack_settings/unacknowledge_timeout_options/'}
                value={slackStore.slackSettings?.unacknowledge_timeout}
                onChange={this.getSlackSettingsChangeHandler('unacknowledge_timeout')}
              />
            </WithPermissionControlTooltip>
          </HorizontalGroup>
        </InlineField>
      </div>
    );
  };

  removeSlackIntegration = async () => {
    const { store } = this.props;
    try {
      await store.slackStore.removeSlackIntegration();
      store.organizationStore.loadCurrentOrganization();
    } catch (err) {
      showApiError(err);
    }
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

    store.organizationStore.loadCurrentOrganization();
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
              Connecting Slack App will allow you to manage alert groups in your team Slack workspace.
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
              src="public/plugins/grafana-oncall-app/assets/img/slack_instructions.png"
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
              <HorizontalGroup spacing="xs" align="center">
                <Icon name="external-link-alt" className={cx('external-link-style')} /> Open Slack connection page
              </HorizontalGroup>
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

export const SlackSettings = withMobXProviderContext(_SlackSettings);
