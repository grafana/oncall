import React from 'react';

import { Button, VerticalGroup } from '@grafana/ui';
import { PluginPage } from 'PluginPage';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import moment from 'moment-timezone';
import LegacyNavHeading from 'navbar/LegacyNavHeading';
import Emoji from 'react-emoji-render';
import { AppRootProps } from 'types';

import GTable from 'components/GTable/GTable';
import Text from 'components/Text/Text';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import MaintenanceForm from 'containers/MaintenanceForm/MaintenanceForm';
import { WithPermissionControl } from 'containers/WithPermissionControl/WithPermissionControl';
import { getAlertReceiveChannelDisplayName } from 'models/alert_receive_channel/alert_receive_channel.helpers';
import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { Maintenance, MaintenanceMode, MaintenanceType } from 'models/maintenance/maintenance.types';
import { pages } from 'pages';
import { WithStoreProps } from 'state/types';
import { UserAction } from 'state/userAction';
import { withMobXProviderContext } from 'state/withStore';

import styles from './Maintenance.module.css';

const cx = cn.bind(styles);

interface MaintenancePageProps extends AppRootProps, WithStoreProps {}

interface MaintenancePageState {
  maintenanceData?: {
    type?: MaintenanceType;
    alert_receive_channel_id?: AlertReceiveChannel['id'];
  };
}

@observer
class MaintenancePage extends React.Component<MaintenancePageProps, MaintenancePageState> {
  state: MaintenancePageState = {};

  async componentDidMount() {
    const {
      store: { alertReceiveChannelStore },
    } = this.props;

    this.update().then(this.parseQueryParams);

    alertReceiveChannelStore.updateItems().then(() => {
      this.forceUpdate();
    });
  }

  componentDidUpdate(prevProps: MaintenancePageProps) {
    if (this.props.query.maintenance_type !== prevProps.query.maintenance_type) {
      this.parseQueryParams();
    }
  }

  parseQueryParams = () => {
    const { query } = this.props;

    if ('maintenance_type' in query) {
      const preselectedMaintenanceType = query.maintenance_type as MaintenanceType;
      const preselectedAlertReceiveChannel = query.alert_receive_channel as AlertReceiveChannel['id'];

      this.setState({
        maintenanceData: {
          type: preselectedMaintenanceType,
          alert_receive_channel_id: preselectedAlertReceiveChannel,
        },
      });
    }
  };

  update = () => {
    const { store } = this.props;
    const { maintenanceStore } = store;

    return maintenanceStore.updateMaintenances();
  };

  render() {
    const { store } = this.props;
    const { maintenanceStore } = store;
    const { maintenanceData } = this.state;

    const data = maintenanceStore?.maintenances;

    const columns = [
      {
        width: 300,
        title: 'Integration',
        render: this.renderTitle,
        key: 'Title',
      },
      {
        width: 200,
        title: 'Mode',
        render: this.renderMode,
        key: 'mode',
      },
      {
        title: 'Progress',
        render: this.renderDuration,
        key: 'progress',
      },
      {
        title: 'Time limit',
        render: this.renderTimer,
        key: 'timer',
      },
      {
        width: 100,
        key: 'action',
        render: this.renderActionButtons,
      },
    ];

    return (
      <PluginPage pageNav={pages['maintenance'].getPageNav()}>
        <div className={cx('root')}>
          <GTable
            emptyText={data ? 'No maintenances found' : 'Loading...'}
            title={() => (
              <div className={cx('header')}>
                <div style={{ display: 'flex', alignItems: 'baseline' }}>
                  <VerticalGroup>
                    <LegacyNavHeading>
                      <Text.Title level={3}>Maintenance</Text.Title>
                    </LegacyNavHeading>
                    <Text type="secondary" className={cx('title')}>
                      Mute noisy sources or use for debugging and avoid bothering your colleagues.
                    </Text>
                  </VerticalGroup>
                </div>
                <WithPermissionControl userAction={UserAction.UpdateMaintenances}>
                  <Button
                    onClick={() => {
                      this.setState({ maintenanceData: {} });
                    }}
                    variant="primary"
                    icon="plus"
                  >
                    Create
                  </Button>
                </WithPermissionControl>
              </div>
            )}
            rowKey="id"
            columns={columns}
            data={data}
          />
        </div>
        {maintenanceData && (
          <MaintenanceForm
            initialData={maintenanceData}
            onUpdate={this.update}
            onHide={() => {
              this.setState({ maintenanceData: undefined });
            }}
          />
        )}
      </PluginPage>
    );
  }

  renderTitle = (maintenance: Maintenance) => {
    const { store } = this.props;
    const { alertReceiveChannelStore } = store;
    const alertReceiveChannel = alertReceiveChannelStore.items
      ? alertReceiveChannelStore.items[maintenance.alert_receive_channel_id]
      : undefined;

    switch (maintenance.type) {
      case MaintenanceType.alert_receive_channel:
        return <Emoji text={getAlertReceiveChannelDisplayName(alertReceiveChannel)} />;

      case MaintenanceType.organization:
        return `${store.teamStore.currentTeam?.name} Team`;
    }
  };

  renderMode = (maintenance: Maintenance) => {
    return maintenance.maintenance_mode === MaintenanceMode.Debug ? 'Debug' : 'Maintenance';
  };

  renderActionButtons = (maintenance: Maintenance) => {
    return (
      <div className={cx('buttons')}>
        <WithPermissionControl userAction={UserAction.UpdateMaintenances}>
          <WithConfirm title="Are you sure to stop?" confirmText="Stop">
            <Button variant="destructive" fill="text" onClick={this.getStopMaintenanceHandler(maintenance)}>
              Stop
            </Button>
          </WithConfirm>
        </WithPermissionControl>
      </div>
    );
  };

  renderDuration = (maintenance: Maintenance) => {
    const started = moment(maintenance.started_at_timestamp * 1000);
    const ended = moment(maintenance.maintenance_till_timestamp * 1000);
    return `${started.format('MMM DD, YYYY hh:mm A')} - ${ended.format('MMM DD, YYYY hh:mm A')}`;
  };

  renderTimer = (maintenance: Maintenance) => {
    return `ends ${moment(maintenance.maintenance_till_timestamp * 1000).fromNow()}`;
  };

  getStopMaintenanceHandler = (maintenance: Maintenance) => {
    const { store } = this.props;
    const { maintenanceStore } = store;

    return () => {
      maintenanceStore.stopMaintenanceMode(maintenance.type, maintenance.alert_receive_channel_id).then(this.update);
    };
  };
}

export default withMobXProviderContext(MaintenancePage);
