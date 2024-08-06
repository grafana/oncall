import React, { Component } from 'react';

import { Button, HorizontalGroup, VerticalGroup, Icon } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import { Block } from 'components/GBlock/Block';
import { PluginLink } from 'components/PluginLink/PluginLink';
import { Text } from 'components/Text/Text';
import { AppFeature } from 'state/features';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import { DOCS_MATTERMOST_SETUP } from 'helpers/consts';
import { showApiError } from 'helpers/helpers';

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
    const envStatus = organizationStore.organizationConfigChecks?.mattermost.env_status;
    const isIntegrated = organizationStore.organizationConfigChecks?.mattermost.is_integrated;

    if (!isIntegrated) {
      return (
        <VerticalGroup spacing="lg">
          <Text.Title level={2}>Connect Mattermost workspace</Text.Title>
          <Block bordered withBackground className={cx('mattermost-infoblock')}>
            <VerticalGroup align="center">
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
            </VerticalGroup>
          </Block>
          {envStatus ? (
            <HorizontalGroup>
              <Button onClick={this.handleOpenMattermostInstructions}>
                <HorizontalGroup spacing="xs" align="center">
                  <Icon name="external-link-alt" className={cx('external-link-style')} /> Open Mattermost connection
                  page
                </HorizontalGroup>
              </Button>
              {store.hasFeature(AppFeature.LiveSettings) && (
                <PluginLink query={{ page: 'live-settings' }}>
                  <Button variant="secondary">See ENV Variables</Button>
                </PluginLink>
              )}
            </HorizontalGroup>
          ) : (
            <HorizontalGroup>
              <PluginLink query={{ page: 'live-settings' }}>
                <Button variant="primary">Setup ENV Variables</Button>
              </PluginLink>
            </HorizontalGroup>
          )}
        </VerticalGroup>
      );
    } else {
      return (
        <VerticalGroup spacing="lg">
          <Text.Title level={2}>Connected Mattermost workspace</Text.Title>
        </VerticalGroup>
      );
    }
  }
}

export const MattermostSettings = withMobXProviderContext(_MattermostSettings);
