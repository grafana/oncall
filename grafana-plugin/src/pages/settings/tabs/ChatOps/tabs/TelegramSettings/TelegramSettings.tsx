import React, { Component } from 'react';

import { css, cx } from '@emotion/css';
import { Badge, Button, Icon, LoadingPlaceholder, Stack, Themeable2, withTheme2 } from '@grafana/ui';
import { DOCS_TELEGRAM_SETUP, StackSize } from 'helpers/consts';
import { observer } from 'mobx-react';

import { Block } from 'components/GBlock/Block';
import { GTable } from 'components/GTable/GTable';
import { PluginLink } from 'components/PluginLink/PluginLink';
import { Text } from 'components/Text/Text';
import { WithConfirm } from 'components/WithConfirm/WithConfirm';
import { TelegramIntegrationButton } from 'containers/TelegramIntegrationButton/TelegramIntegrationButton';
import { TelegramColorIcon } from 'icons/Icons';
import { TelegramChannel } from 'models/telegram_channel/telegram_channel.types';
import { AppFeature } from 'state/features';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';

interface TelegramProps extends WithStoreProps, Themeable2 {}

interface TelegramState {}

@observer
class _TelegramSettings extends Component<TelegramProps, TelegramState> {
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
    const styles = getStyles();

    const telegramConfigured = organizationStore.currentOrganization?.env_status.telegram_configured;

    if (!telegramConfigured && store.hasFeature(AppFeature.LiveSettings)) {
      return (
        <Stack direction="column" gap={StackSize.lg}>
          <Text.Title level={2}>Connect Telegram workspace</Text.Title>
          <Block bordered withBackground className={cx('telegram-infoblock')}>
            <Stack direction="column" alignItems="center">
              <div className={styles.infoblockIcon}>
                <TelegramColorIcon />
              </div>
              <Text className={styles.infoBlockText}>
                You can manage alert groups in your team Telegram channel or from personal direct messages.{' '}
              </Text>

              <Text className={styles.infoBlockText}>
                To connect channel setup Telegram environment first, which includes connection to your bot and host URL.
              </Text>
              <Text type="secondary" className={styles.infoBlockText}>
                More details in{' '}
                <a href={DOCS_TELEGRAM_SETUP} target="_blank" rel="noreferrer">
                  <Text type="link">our documentation</Text>
                </a>
              </Text>
            </Stack>
          </Block>
          <PluginLink query={{ page: 'live-settings' }}>
            <Button variant="primary">Setup ENV Variables</Button>
          </PluginLink>
        </Stack>
      );
    }

    if (!connectedChannels) {
      return <LoadingPlaceholder text="Loading..." />;
    }

    if (!connectedChannels.length) {
      return (
        <Stack direction="column" gap={StackSize.lg}>
          <Text.Title level={2}>Connect Telegram workspace</Text.Title>
          <Block bordered withBackground className={styles.telegramInfoBlock}>
            <Stack direction="column" alignItems="center">
              <div className={styles.infoblockIcon}>
                <TelegramColorIcon />
              </div>
              <Text className={styles.infoBlockText}>
                You can manage alert groups in your team Telegram channel or from personal direct messages.{' '}
              </Text>
              <Text type="secondary" className={styles.infoBlockText}>
                More details in{' '}
                <a href={DOCS_TELEGRAM_SETUP} target="_blank" rel="noreferrer">
                  <Text type="link">our documentation</Text>
                </a>
              </Text>
            </Stack>
          </Block>
          <Text>
            <Text.Title level={4}>Features</Text.Title>
            <div className={styles.featuresList}>
              <ul>
                <li>perform actions (acknowledge, resolve, silence)</li>
                <li>discuss alerts in comments</li>
                <li>notifications to users accounts will be served as links to the main channel</li>
              </ul>
            </div>
            Make sure your team connects Telegram in their OnCall user profiles too or they cannot manage alert groups.
          </Text>
          <Stack>
            <TelegramIntegrationButton size="md" onUpdate={this.update} />
            {store.hasFeature(AppFeature.LiveSettings) && (
              <PluginLink query={{ page: 'live-settings' }}>
                <Button variant="secondary">See ENV Variables</Button>
              </PluginLink>
            )}
          </Stack>
        </Stack>
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
          <div className={styles.root}>
            <GTable
              title={() => (
                <div className={styles.header}>
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
      <Stack justifyContent="flex-end">
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
      </Stack>
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

export const TelegramSettings = withMobXProviderContext(withTheme2(_TelegramSettings));

const getStyles = () => {
  return {
    root: css`
      display: block;
    `,

    header: css`
      display: flex;
      justify-content: space-between;
    `,

    telegramInfoBlock: css`
      text-align: center;
      width: 725px;
    `,

    featuresList: css`
      > ul {
        margin: 20px 30px;
      }
    `,

    infoBlockText: css`
      margin-left: 48px;
      margin-right: 48px;
      margin-top: 24px;
    `,

    infoblockIcon: css`
      margin-top: 24px;
    `,
  };
};
