import React, { Component } from 'react';

import { Alert, Button, HorizontalGroup, Icon, LoadingPlaceholder, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import GTable from 'components/GTable/GTable';
import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import Tutorial from 'components/Tutorial/Tutorial';
import { TutorialStep } from 'components/Tutorial/Tutorial.types';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import TelegramIntegrationButton from 'containers/TelegramIntegrationButton/TelegramIntegrationButton';
import { TelegramChannel } from 'models/telegram_channel/telegram_channel.types';
import { AppFeature } from 'state/features';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';

import styles from './TelegramSettings.module.css';

const cx = cn.bind(styles);

interface TelegramProps extends WithStoreProps {}

interface TelegramState {}

@observer
class TelegramSettings extends Component<TelegramProps, TelegramState> {
  state: TelegramState = {};

  componentDidMount() {
    this.update();
  }

  update = () => {
    const { telegramChannelStore } = this.props.store;
    telegramChannelStore.updateItems();
  };

  render() {
    const { hasFeature, telegramChannelStore, teamStore } = this.props.store;
    const connectedChannels = telegramChannelStore.getSearchResult();

    const telegramConfigured = teamStore.currentTeam?.env_status.telegram_configured;

    if (!telegramConfigured && hasFeature(AppFeature.LiveSettings)) {
      return (
        <Alert
          severity="warning"
          // @ts-ignore
          title={
            <>
              Can't connect Telegram. <PluginLink query={{ page: 'live-settings' }}> Check ENV variables</PluginLink>{' '}
              related to Telegram.
            </>
          }
        />
      );
    }

    if (!connectedChannels) {
      return <LoadingPlaceholder text="Loading..." />;
    }

    if (!connectedChannels.length) {
      return (
        <Tutorial
          step={TutorialStep.Slack}
          title={
            <VerticalGroup align="center" spacing="lg">
              <Text type="secondary">
                Bring the whole incident lifecycle into your chat workspace. Everything from alerts, monitoring, and
                escalations to reports.
              </Text>
              <TelegramIntegrationButton size="lg" onUpdate={this.update} />
            </VerticalGroup>
          }
        />
      );
    }

    const columns = [
      {
        width: '30%',
        title: 'Channel name',
        dataIndex: 'channel_name',
      },
      {
        width: '30%',
        title: 'Discussion group name',
        dataIndex: 'discussion_group_name',
      },
      {
        width: '10%',
        title: 'Is default channel',
        dataIndex: 'is_default_channel',
        render: this.renderDefaultChannel,
      },
      {
        width: '30%',
        key: 'action',
        render: this.renderActionButtons,
      },
    ];
    return (
      <div>
        {connectedChannels && (
          <div className={cx('root')}>
            <GTable
              title={() => (
                <div className={cx('header')}>
                  <Text.Title level={3}>Telegram Channels</Text.Title>
                  <TelegramIntegrationButton onUpdate={this.update} />
                </div>
              )}
              emptyText={connectedChannels ? 'No Telegram channels connected' : 'Loading...'}
              rowKey="id"
              columns={columns}
              data={connectedChannels}
            />
          </div>
        )}
      </div>
    );
  }

  renderDefaultChannel = (isDefault: boolean) => {
    return <>{isDefault && <Icon name="check" />}</>;
  };

  renderActionButtons = (record: TelegramChannel) => {
    return (
      <HorizontalGroup justify="flex-end">
        <Button
          onClick={() => this.makeTelegramChannelDefault(record.id)}
          disabled={record.is_default_channel}
          fill="text"
        >
          Make default
        </Button>
        <WithConfirm title="Are you sure to disconnect?">
          <Button onClick={() => this.disconnectTelegramChannelDefault(record.id)} fill="text" variant="destructive">
            Disconnect
          </Button>
        </WithConfirm>
      </HorizontalGroup>
    );
  };

  makeTelegramChannelDefault = async (id: TelegramChannel['id']) => {
    const { telegramChannelStore } = this.props.store;

    await telegramChannelStore.makeTelegramChannelDefault(id);
    telegramChannelStore.updateItems();
  };

  disconnectTelegramChannelDefault = async (id: TelegramChannel['id']) => {
    const { telegramChannelStore } = this.props.store;

    await telegramChannelStore.deleteTelegramChannel(id);
    telegramChannelStore.updateItems();
  };
}

export default withMobXProviderContext(TelegramSettings);
