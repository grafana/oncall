import React, { Component } from 'react';

import {Button, HorizontalGroup, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import { Block } from 'components/GBlock/Block';
import { PluginLink } from 'components/PluginLink/PluginLink';
import { Text } from 'components/Text/Text';
import { MattermostSetupButton } from 'containers/MattermostSetupButton/MattermostSetupButton';
import { AppFeature } from 'state/features';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import { DOCS_MATTERMOST_SETUP } from 'utils/consts';

import styles from './MattermostSettings.module.css'

const cx = cn.bind(styles)

interface MattermostProps extends WithStoreProps {}

interface MattermostState {}

@observer
class MattermostSettings extends Component<MattermostProps, MattermostState> {
  state: MattermostState = {};

  update = () => {}

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
                You can manage alert groups in your team Mattermost channel or from personal direct messages.{' '}
              </Text>

              <Text className={cx('infoblock-text')}>
                To connect channel setup Mattermost environment first, which includes connection to your bot and host URL.
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
              <MattermostSetupButton size='md' onUpdate={this.update} />
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
      )
    }
  }
}
export default withMobXProviderContext(MattermostSettings);
