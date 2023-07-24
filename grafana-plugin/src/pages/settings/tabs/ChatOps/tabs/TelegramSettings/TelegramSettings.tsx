import React, { Component } from 'react';

import { Badge, Button, HorizontalGroup, Icon, LoadingPlaceholder, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import Block from 'components/GBlock/Block';
import GTable from 'components/GTable/GTable';
import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import TelegramIntegrationButton from 'containers/TelegramIntegrationButton/TelegramIntegrationButton';
import { TelegramColorIcon } from 'icons';
import { TelegramChannel } from 'models/telegram_channel/telegram_channel.types';
import { AppFeature } from 'state/features';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import { DOCS_TELEGRAM_SETUP } from 'utils/consts';

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
    const { store } = this.props;

    store.telegramChannelStore.updateItems();
  };

  render() {
    const { store } = this.props;
    const { telegramChannelStore, organizationStore } = store;
    const connectedChannels = telegramChannelStore.getSearchResult();

    const telegramConfigured = organizationStore.currentOrganization?.env_status.telegram_configured;

    if (!telegramConfigured && store.hasFeature(AppFeature.LiveSettings)) {
      return (
        <VerticalGroup spacing="lg">
          <Text.Title level={2}>Connect Telegram workspace</Text.Title>
          <Block bordered withBackground className={cx('telegram-infoblock')}>
            <VerticalGroup align="center">
              <div className={cx('infoblock-icon')}>
                <TelegramColorIcon />
              </div>
              <Text className={cx('infoblock-text')}>
                You can manage alert groups in your team Telegram channel or from personal direct messages.{' '}
              </Text>

              <Text className={cx('infoblock-text')}>
                To connect channel setup Telegram environment first, which includes connection to your bot and host URL.
              </Text>
              <Text type="secondary" className={cx('infoblock-text')}>
                More details in{' '}
                <a href={DOCS_TELEGRAM_SETUP} target="_blank" rel="noreferrer">
                  <Text type="link">our documentation</Text>
                </a>
              </Text>
            </VerticalGroup>
          </Block>
          <PluginLink query={{ page: 'live-settings' }}>
            <Button variant="primary">Setup ENV Variables</Button>
          </PluginLink>
        </VerticalGroup>
      );
    }

    if (!connectedChannels) {
      return <LoadingPlaceholder text="Loading..." />;
    }

    if (!connectedChannels.length) {
      return (
        <VerticalGroup spacing="lg">
          <Text.Title level={2}>Connect Telegram workspace</Text.Title>
          <Block bordered withBackground className={cx('telegram-infoblock')}>
            <VerticalGroup align="center">
              <div className={cx('infoblock-icon')}>
                <TelegramColorIcon />
              </div>
              <Text className={cx('infoblock-text')}>
                You can manage alert groups in your team Telegram channel or from personal direct messages.{' '}
              </Text>
              <Text type="secondary" className={cx('infoblock-text')}>
                More details in{' '}
                <a href={DOCS_TELEGRAM_SETUP} target="_blank" rel="noreferrer">
                  <Text type="link">our documentation</Text>
                </a>
              </Text>
            </VerticalGroup>
          </Block>
          <Text>
            <Text.Title level={4}>Features</Text.Title>
            <div className={cx('features-list')}>
              <ul>
                <li>perform actions (acknowledge, resolve, silence)</li>
                <li>discuss alerts in comments</li>
                <li>notifications to users accounts will be served as links to the main channel</li>
              </ul>
            </div>
            Make sure your team connects Telegram in their OnCall user profiles too or they cannot manage alert groups.
          </Text>
          <HorizontalGroup>
            <TelegramIntegrationButton size="md" onUpdate={this.update} />
            {store.hasFeature(AppFeature.LiveSettings) && (
              <PluginLink query={{ page: 'live-settings' }}>
                <Button variant="secondary">See ENV Variables</Button>
              </PluginLink>
            )}
          </HorizontalGroup>
        </VerticalGroup>
      );
    }

    const columns = [
      {
        width: '35%',
        title: 'Channel',
        key: 'name',
        render: this.renderChannelName,
      },
      {
        width: '35%',
        title: 'Discussion group',
        dataIndex: 'discussion_group_name',
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

  renderChannelName = (record: TelegramChannel) => {
    return (
      <>
        {record.channel_name} {record.is_default_channel && <Badge text="Default" color="green" />}
      </>
    );
  };
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
    const { store } = this.props;
    const { telegramChannelStore } = store;

    await telegramChannelStore.makeTelegramChannelDefault(id);
    telegramChannelStore.updateItems();
  };

  disconnectTelegramChannelDefault = async (id: TelegramChannel['id']) => {
    const { store } = this.props;
    const { telegramChannelStore } = store;

    await telegramChannelStore.deleteTelegramChannel(id);
    telegramChannelStore.updateItems();
  };
}

export default withMobXProviderContext(TelegramSettings);
