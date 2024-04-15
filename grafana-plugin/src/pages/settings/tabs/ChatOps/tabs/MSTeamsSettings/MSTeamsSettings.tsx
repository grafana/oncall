import React, { Component } from 'react';

import { Button, HorizontalGroup, LoadingPlaceholder, Badge } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import { GTable } from 'components/GTable/GTable';
import { Text } from 'components/Text/Text';
import { WithConfirm } from 'components/WithConfirm/WithConfirm';
import { MSTeamsInstructions } from 'containers/MSTeams/MSTeamsInstructions';
import { MSTeamsIntegrationButton } from 'containers/MSTeamsIntegrationButton/MSTeamsIntegrationButton';
import { MSTeamsChannel } from 'models/msteams_channel/msteams_channel.types';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';

import styles from 'pages/settings/tabs/ChatOps/tabs/MSTeamsSettings/MSTeamsSettings.module.css';

const cx = cn.bind(styles);

interface MSTeamsProps extends WithStoreProps {}

interface MSTeamsState {
  verificationCode: string;
}

@observer
class MSTeamsSettings extends Component<MSTeamsProps, MSTeamsState> {
  state: MSTeamsState = {
    verificationCode: '',
  };

  componentDidMount() {
    this.update();
  }

  update = async () => {
    const { store } = this.props;
    const data = await store.msteamsChannelStore.getMSTeamsChannelVerificationCode();
    this.setState({ verificationCode: data });
    store.msteamsChannelStore.updateItems();
  };

  render() {
    const { store } = this.props;
    const { msteamsChannelStore } = store;
    const { verificationCode } = this.state;

    const connectedChannels = msteamsChannelStore.getSearchResult();

    if (!connectedChannels) {
      return <LoadingPlaceholder text="Loading..." />;
    }

    if (!connectedChannels.length) {
      return (
        <>
          <MSTeamsInstructions showInfoBox verificationCode={verificationCode} />
        </>
      );
    }

    const columns = [
      {
        width: '40%',
        title: 'Team',
        dataIndex: 'team',
      },
      {
        width: '30%',
        title: 'Channel name',
        render: this.renderDefaultBadge,
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
                  <Text.Title level={3}>Microsoft Teams Channels</Text.Title>
                  <MSTeamsIntegrationButton onUpdate={this.update} />
                </div>
              )}
              emptyText={connectedChannels ? 'No Microsoft Teams channels connected' : 'Loading...'}
              rowKey="id"
              columns={columns}
              data={connectedChannels}
            />
          </div>
        )}
      </div>
    );
  }

  renderActionButtons = (record: MSTeamsChannel) => {
    return (
      <HorizontalGroup justify="flex-end">
        <Button
          onClick={() => this.setChannelAsDefault(record.id)}
          disabled={record.is_default}
          fill="outline"
          size="sm"
        >
          Make default
        </Button>
        <WithConfirm title="Are you sure to disconnect?">
          <Button onClick={() => this.unsetChannelAsDefault(record.id)} fill="outline" variant="destructive" size="sm">
            Disconnect
          </Button>
        </WithConfirm>
      </HorizontalGroup>
    );
  };

  renderDefaultBadge = (record: MSTeamsChannel) => {
    return (
      <>
        {record.name} {record.is_default && <Badge text="Default" color="green" />}
      </>
    );
  };

  setChannelAsDefault = async (id: MSTeamsChannel['id']) => {
    const { store } = this.props;
    const { msteamsChannelStore } = store;

    await msteamsChannelStore.makeMSTeamsChannelDefault(id);
    msteamsChannelStore.updateItems();
  };

  unsetChannelAsDefault = async (id: MSTeamsChannel['id']) => {
    const { store } = this.props;
    const { msteamsChannelStore } = store;

    await msteamsChannelStore.deleteMSTeamsChannel(id);
    msteamsChannelStore.updateItems();
  };
}

export default withMobXProviderContext(MSTeamsSettings);
