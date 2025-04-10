import React, { Component } from 'react';

import { css } from '@emotion/css';
import { Badge, Button, LoadingPlaceholder, Stack } from '@grafana/ui';
import { DOCS_MATTERMOST_SETUP, StackSize } from 'helpers/consts';
import { observer } from 'mobx-react';

import { Block } from 'components/GBlock/Block';
import { GTable } from 'components/GTable/GTable';
import { PluginLink } from 'components/PluginLink/PluginLink';
import { Text } from 'components/Text/Text';
import { WithConfirm } from 'components/WithConfirm/WithConfirm';
import { MattermostIntegrationButton } from 'containers/MattermostIntegrationButton/MattermostIntegrationButton';
import { MattermostChannel } from 'models/mattermost/mattermost.types';
import { AppFeature } from 'state/features';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';

interface MattermostProps extends WithStoreProps {}

interface MattermostState {}

@observer
class _MattermostSettings extends Component<MattermostProps, MattermostState> {
  state: MattermostState = {};

  componentDidMount() {
    this.update();
  }

  update = () => {
    const { store } = this.props;

    store.mattermostChannelStore.updateItems();
  };

  render() {
    const { store } = this.props;
    const { mattermostChannelStore, organizationStore } = store;
    const connectedChannels = mattermostChannelStore.getSearchResult();
    const styles = getStyles();

    const mattermostConfigured = organizationStore.currentOrganization?.env_status.mattermost_configured;

    if (!mattermostConfigured && store.hasFeature(AppFeature.LiveSettings)) {
      return (
        <Stack direction="column" gap={StackSize.lg}>
          <Text.Title level={2}>Connect Mattermost workspace</Text.Title>
          <Block bordered withBackground className={styles.mattermostInfoBlock}>
            <Stack direction="column" alignItems="center">
              <Text className={styles.infoBlockText}>
                Connecting Mattermost App will allow you to manage alert groups in your team Mattermost workspace.
              </Text>

              <Text className={styles.infoBlockText}>
                After a basic workspace connection your team members need to connect their personal Mattermost accounts
                in order to be allowed to manage alert groups.
              </Text>
              <Text type="secondary" className={styles.infoBlockText}>
                More details in{' '}
                <a href={DOCS_MATTERMOST_SETUP} target="_blank" rel="noreferrer">
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
          <Text.Title level={2}>Connect Mattermost workspace</Text.Title>
          <Block bordered withBackground className={styles.mattermostInfoBlock}>
            <Stack direction="column" alignItems="center">
              <Text className={styles.infoBlockText}>
                Connecting Mattermost App will allow you to manage alert groups in your team Mattermost workspace.
              </Text>

              <Text className={styles.infoBlockText}>
                After a basic workspace connection your team members need to connect their personal Mattermost accounts
                in order to be allowed to manage alert groups.
              </Text>
              <Text type="secondary" className={styles.infoBlockText}>
                More details in{' '}
                <a href={DOCS_MATTERMOST_SETUP} target="_blank" rel="noreferrer">
                  <Text type="link">our documentation</Text>
                </a>
              </Text>
            </Stack>
          </Block>
          <Stack>
            <MattermostIntegrationButton size="md" onUpdate={this.update} />
            {store.hasFeature(AppFeature.LiveSettings) && (
              <PluginLink query={{ page: 'live-settings' }}>
                <Button variant="primary">See ENV Variables</Button>
              </PluginLink>
            )}
          </Stack>
        </Stack>
      );
    }

    const columns = [
      {
        width: '35%',
        title: 'Channel Name',
        key: 'name',
        render: this.renderChannelName,
      },
      {
        width: '35%',
        title: 'Channel ID',
        render: this.renderChannelId,
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
                  <Text.Title level={3}>Mattermost Channels</Text.Title>
                  <MattermostIntegrationButton onUpdate={this.update} />
                </div>
              )}
              emptyText={connectedChannels ? 'No Mattermost channels connected' : 'Loading...'}
              rowKey="id"
              columns={columns}
              data={connectedChannels}
            />
          </div>
        )}
      </div>
    );
  }

  renderChannelName = (record: MattermostChannel) => {
    return (
      <>
        {record.display_name} {record.is_default_channel && <Badge text="Default" color="green" />}
      </>
    );
  };

  renderChannelId = (record: MattermostChannel) => {
    return <>{record.channel_id}</>;
  };

  renderActionButtons = (record: MattermostChannel) => {
    return (
      <Stack justifyContent="flex-end">
        <Button
          onClick={() => this.makeMattermostChannelDefault(record.id)}
          disabled={record.is_default_channel}
          fill="text"
        >
          Make default
        </Button>
        <WithConfirm title="Are you sure to disconnect?">
          <Button onClick={() => this.disconnectMattermostChannel(record.id)} fill="text" variant="destructive">
            Disconnect
          </Button>
        </WithConfirm>
      </Stack>
    );
  };

  makeMattermostChannelDefault = async (id: MattermostChannel['id']) => {
    const { store } = this.props;
    const { mattermostChannelStore } = store;

    await mattermostChannelStore.makeMattermostChannelDefault(id);
    mattermostChannelStore.updateItems();
  };

  disconnectMattermostChannel = async (id: MattermostChannel['id']) => {
    const { store } = this.props;
    const { mattermostChannelStore } = store;

    await mattermostChannelStore.deleteMattermostChannel(id);
    mattermostChannelStore.updateItems();
  };
}

export const MattermostSettings = withMobXProviderContext(_MattermostSettings);

const getStyles = () => {
  return {
    root: css`
      display: block;
    `,
    header: css`
      display: flex;
      justify-content: space-between;
    `,
    mattermostInfoBlock: css`
      text-align: center;
      width: 725px;
    `,

    infoBlockText: css`
      margin-left: 48px;
      margin-right: 48px;
      margin-top: 24px;
    `,
  };
};
