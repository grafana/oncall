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
import { DesktopChannel } from 'models/desktop_channel/desktop_channel.types';
import { AppFeature } from 'state/features';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';

import styles from './DesktopSettings.module.css';

const cx = cn.bind(styles);

interface DesktopProps extends WithStoreProps {}

interface DesktopState {}

@observer
class DesktopSettings extends Component<DesktopProps, DesktopState> {
  state: DesktopState = {};

  componentDidMount() {
    this.update();
  }

  update = () => {
    const { store } = this.props;

    store.desktopChannelStore.updateItems();
  };

  render() {
    const { store } = this.props;
    const { desktopChannelStore, teamStore } = store;
    const connectedChannels = desktopChannelStore.getSearchResult();

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
            </VerticalGroup>
          }
        />
      );
    }

    const columns = [
      {
        width: '60%',
        title: 'Channel name',
        dataIndex: 'name',
      },
      {
        width: '10%',
        title: 'Is default channel',
        dataIndex: 'is_default',
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
                  <Text.Title level={3}>Channels</Text.Title>
                </div>
              )}
              emptyText={connectedChannels ? 'No channels connected' : 'Loading...'}
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

  renderActionButtons = (record: DesktopChannel) => {
    return (
      <HorizontalGroup justify="flex-end">
        <Button fill="text">
          Make default
        </Button>
        <WithConfirm title="Are you sure to disconnect?">
          <Button fill="text" variant="destructive">
            Disconnect
          </Button>
        </WithConfirm>
      </HorizontalGroup>
    );
  };
}

export default withMobXProviderContext(DesktopSettings);
