import React, { Component } from 'react';

import { Button, Stack, Icon } from '@grafana/ui';
import cn from 'classnames/bind';
import { DOCS_MATTERMOST_SETUP, StackSize } from 'helpers/consts';
import { showApiError } from 'helpers/helpers';
import { observer } from 'mobx-react';

import { Block } from 'components/GBlock/Block';
import { PluginLink } from 'components/PluginLink/PluginLink';
import { Text } from 'components/Text/Text';
import { AppFeature } from 'state/features';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';

import styles from './MattermostSettings.module.css';

const cx = cn.bind(styles);

interface MattermostProps extends WithStoreProps {}

interface MattermostState {}

@observer
class _MattermostSettings extends Component<MattermostProps, MattermostState> {
  state: MattermostState = {};

  handleOpenMattermostInstructions = async () => {
    const { store } = this.props;
    try {
      await store.mattermostStore.installMattermostIntegration();
    } catch (err) {
      showApiError(err);
    }
  };

  render() {
    const { store } = this.props;
    const { organizationStore } = store;
    const envStatus = organizationStore.currentOrganization?.env_status.mattermost_configured;
    const isIntegrated = false; // TODO: Check if integration is configured and can show channels view

    if (!isIntegrated) {
      return (
        <Stack direction="column" gap={StackSize.lg}>
          <Text.Title level={2}>Connect Mattermost workspace</Text.Title>
          <Block bordered withBackground className={cx('mattermost-infoblock')}>
            <Stack direction="column" alignItems="center">
              <Text className={cx('infoblock-text')}>
                Connecting Mattermost App will allow you to manage alert groups in your team Mattermost workspace.
              </Text>

              <Text className={cx('infoblock-text')}>
                After a basic workspace connection your team members need to connect their personal Mattermost accounts
                in order to be allowed to manage alert groups.
              </Text>
              <Text type="secondary" className={cx('infoblock-text')}>
                More details in{' '}
                <a href={DOCS_MATTERMOST_SETUP} target="_blank" rel="noreferrer">
                  <Text type="link">our documentation</Text>
                </a>
              </Text>
            </Stack>
          </Block>
          {envStatus ? (
            <Stack>
              <Button onClick={this.handleOpenMattermostInstructions}>
                <Stack gap={StackSize.xs} alignItems="center">
                  <Icon name="external-link-alt" className="u-margin-left-xs u-margin-bottom-xxs" /> Open Mattermost
                  connection page
                </Stack>
              </Button>
              {store.hasFeature(AppFeature.LiveSettings) && (
                <PluginLink query={{ page: 'live-settings' }}>
                  <Button variant="secondary">See ENV Variables</Button>
                </PluginLink>
              )}
            </Stack>
          ) : (
            <Stack>
              <PluginLink query={{ page: 'live-settings' }}>
                <Button variant="primary">Setup ENV Variables</Button>
              </PluginLink>
            </Stack>
          )}
        </Stack>
      );
    } else {
      return (
        <Stack direction="column" gap={StackSize.lg}>
          <Text.Title level={2}>Connected Mattermost workspace</Text.Title>
        </Stack>
      );
    }
  }
}

export const MattermostSettings = withMobXProviderContext(_MattermostSettings);
