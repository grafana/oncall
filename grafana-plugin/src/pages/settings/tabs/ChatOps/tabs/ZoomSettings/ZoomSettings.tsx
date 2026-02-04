import React, { Component } from 'react';

import { css } from '@emotion/css';
import { Badge, Button, LoadingPlaceholder, Stack } from '@grafana/ui';
import { DOCS_ZOOM_SETUP, StackSize } from 'helpers/consts';
import { observer } from 'mobx-react';

import { Block } from 'components/GBlock/Block';
import { GTable } from 'components/GTable/GTable';
import { PluginLink } from 'components/PluginLink/PluginLink';
import { Text } from 'components/Text/Text';
import { WithConfirm } from 'components/WithConfirm/WithConfirm';
import { ZoomIntegrationButton } from 'containers/ZoomIntegrationButton/ZoomIntegrationButton';
import { ZoomChannel } from 'models/zoom/zoom.types';
import { AppFeature } from 'state/features';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';

interface ZoomProps extends WithStoreProps {}

interface ZoomState {}

@observer
class _ZoomSettings extends Component<ZoomProps, ZoomState> {
  state: ZoomState = {};

  componentDidMount() {
    this.update();
  }

  update = () => {
    const { store } = this.props;

    store.zoomChannelStore.updateItems();
  };

  render() {
    const { store } = this.props;
    const { zoomChannelStore, organizationStore } = store;
    const connectedChannels = zoomChannelStore.getSearchResult();
    const styles = getStyles();

    const zoomConfigured = organizationStore.currentOrganization?.env_status.zoom_configured;

    if (!zoomConfigured && store.hasFeature(AppFeature.LiveSettings)) {
      return (
        <Stack direction="column" gap={StackSize.lg}>
          <Text.Title level={2}>Connect Zoom workspace</Text.Title>
          <Block bordered withBackground className={styles.zoomInfoBlock}>
            <Stack direction="column" alignItems="center">
              <Text className={styles.infoBlockText}>
                Connecting Zoom App will allow you to manage alert groups in your team Zoom Team Chat.
              </Text>

              <Text className={styles.infoBlockText}>
                After a basic workspace connection your team members need to connect their personal Zoom accounts in
                order to be allowed to manage alert groups.
              </Text>
              <Text type="secondary" className={styles.infoBlockText}>
                More details in{' '}
                <a href={DOCS_ZOOM_SETUP} target="_blank" rel="noreferrer">
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
          <Text.Title level={2}>Connect Zoom workspace</Text.Title>
          <Block bordered withBackground className={styles.zoomInfoBlock}>
            <Stack direction="column" alignItems="center">
              <Text className={styles.infoBlockText}>
                Connecting Zoom App will allow you to manage alert groups in your team Zoom Team Chat.
              </Text>

              <Text className={styles.infoBlockText}>
                After a basic workspace connection your team members need to connect their personal Zoom accounts in
                order to be allowed to manage alert groups.
              </Text>
              <Text type="secondary" className={styles.infoBlockText}>
                More details in{' '}
                <a href={DOCS_ZOOM_SETUP} target="_blank" rel="noreferrer">
                  <Text type="link">our documentation</Text>
                </a>
              </Text>
            </Stack>
          </Block>
          <Stack>
            <ZoomIntegrationButton size="md" onUpdate={this.update} />
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
                  <Text.Title level={3}>Zoom Channels</Text.Title>
                  <ZoomIntegrationButton onUpdate={this.update} />
                </div>
              )}
              emptyText={connectedChannels ? 'No Zoom channels connected' : 'Loading...'}
              rowKey="id"
              columns={columns}
              data={connectedChannels}
            />
          </div>
        )}
      </div>
    );
  }

  renderChannelName = (record: ZoomChannel) => {
    return (
      <>
        {record.channel_name} {record.is_default_channel && <Badge text="Default" color="green" />}
      </>
    );
  };

  renderChannelId = (record: ZoomChannel) => {
    return <>{record.channel_id}</>;
  };

  renderActionButtons = (record: ZoomChannel) => {
    return (
      <Stack justifyContent="flex-end">
        <Button onClick={() => this.makeZoomChannelDefault(record.id)} disabled={record.is_default_channel} fill="text">
          Make default
        </Button>
        <WithConfirm title="Are you sure to disconnect?">
          <Button onClick={() => this.disconnectZoomChannel(record.id)} fill="text" variant="destructive">
            Disconnect
          </Button>
        </WithConfirm>
      </Stack>
    );
  };

  makeZoomChannelDefault = async (id: ZoomChannel['id']) => {
    const { store } = this.props;
    const { zoomChannelStore } = store;

    await zoomChannelStore.makeZoomChannelDefault(id);
    zoomChannelStore.updateItems();
  };

  disconnectZoomChannel = async (id: ZoomChannel['id']) => {
    const { store } = this.props;
    const { zoomChannelStore } = store;

    await zoomChannelStore.deleteZoomChannel(id);
    zoomChannelStore.updateItems();
  };
}

export const ZoomSettings = withMobXProviderContext(_ZoomSettings);

const getStyles = () => {
  return {
    root: css`
      display: block;
    `,
    header: css`
      display: flex;
      justify-content: space-between;
    `,
    zoomInfoBlock: css`
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
