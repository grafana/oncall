import React from 'react';

import { AppRootProps } from '@grafana/data';
import { getLocationSrv } from '@grafana/runtime';
import { Button, LoadingPlaceholder, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { debounce } from 'lodash-es';
import { observer } from 'mobx-react';

import GList from 'components/GList/GList';
import IntegrationsFilters, { Filters } from 'components/IntegrationsFilters/IntegrationsFilters';
import Text from 'components/Text/Text';
import Tutorial from 'components/Tutorial/Tutorial';
import { TutorialStep } from 'components/Tutorial/Tutorial.types';
import AlertReceiveChannelCard from 'containers/AlertReceiveChannelCard/AlertReceiveChannelCard';
import AlertRules from 'containers/AlertRules/AlertRules';
import CreateAlertReceiveChannelContainer from 'containers/CreateAlertReceiveChannelContainer/CreateAlertReceiveChannelContainer';
import IntegrationSettings from 'containers/IntegrationSettings/IntegrationSettings';
import { IntegrationSettingsTab } from 'containers/IntegrationSettings/IntegrationSettings.types';
import { WithPermissionControl } from 'containers/WithPermissionControl/WithPermissionControl';
import { AlertReceiveChannel } from 'models/alert_receive_channel';
import { AlertReceiveChannelOption } from 'models/alert_receive_channel/alert_receive_channel.types';
import { WithStoreProps } from 'state/types';
import { UserAction } from 'state/userAction';
import { withMobXProviderContext } from 'state/withStore';
import { openWarningNotification } from 'utils';

import styles from './Integrations.module.css';

const cx = cn.bind(styles);

interface IntegrationsState {
  integrationsFilters: Filters;
  showCreateIntegrationModal: boolean;
  alertReceiveChannelToShowSettings?: AlertReceiveChannel['id'];
  integrationSettingsTab?: IntegrationSettingsTab;
}

interface IntegrationsProps extends WithStoreProps, AppRootProps {}

@observer
class Integrations extends React.Component<IntegrationsProps, IntegrationsState> {
  state: IntegrationsState = {
    integrationsFilters: { searchTerm: '' },
    showCreateIntegrationModal: false,
  };

  alertReceiveChanneltoPoll: { [key: string]: number } = {};
  alertReceiveChannelTimerId: ReturnType<typeof setTimeout>;

  async componentDidMount() {
    this.update().then(this.parseQueryParams);
  }

  setSelectedAlertReceiveChannel = (alertReceiveChannelId: AlertReceiveChannel['id']) => {
    const { store } = this.props;
    store.selectedAlertReceiveChannel = alertReceiveChannelId;
    getLocationSrv().update({ partial: true, query: { id: alertReceiveChannelId } });
  };

  parseQueryParams = () => {
    const { store, query } = this.props;

    const { alertReceiveChannelStore } = store;

    const searchResult = alertReceiveChannelStore.getSearchResult();
    let selectedAlertReceiveChannel = store.selectedAlertReceiveChannel;
    if (query.id) {
      const alertReceiveChannelId = searchResult && searchResult.find((res) => res.id === query?.id)?.id;
      if (alertReceiveChannelId) {
        selectedAlertReceiveChannel = alertReceiveChannelId;
      } else {
        openWarningNotification(
          `Integration with id=${query?.id} is not found. Please select integration from the list.`
        );
      }
      if (query.tab) {
        this.setState({ integrationSettingsTab: query.tab });
        this.setState({ alertReceiveChannelToShowSettings: query.id });
      }
    }
    if (!selectedAlertReceiveChannel) {
      selectedAlertReceiveChannel = searchResult[0]?.id;
    }
    this.setSelectedAlertReceiveChannel(selectedAlertReceiveChannel);
  };

  update = () => {
    const { store } = this.props;
    return store.alertReceiveChannelStore.updateItems();
  };

  componentDidUpdate(prevProps: IntegrationsProps) {
    if (this.props.query.id !== prevProps.query.id) {
      this.parseQueryParams();
    }
    if (this.props.query.tab !== prevProps.query.tab) {
      this.parseQueryParams();
    }
  }

  componentWillUnmount() {
    clearInterval(this.alertReceiveChannelTimerId);
  }

  render() {
    const { store } = this.props;
    const {
      integrationsFilters: { searchTerm },
    } = this.state;
    const {
      integrationsFilters,
      alertReceiveChannelToShowSettings,
      integrationSettingsTab,
      showCreateIntegrationModal,
    } = this.state;
    const { alertReceiveChannelStore } = store;
    const searchResult = alertReceiveChannelStore.getSearchResult();

    return (
      <>
        <div className={cx('root')}>
          <div className={cx('filters')}>
            <IntegrationsFilters value={integrationsFilters} onChange={this.handleIntegrationsFiltersChange} />
          </div>
          {searchResult?.length ? (
            <div className={cx('integrations')}>
              <div className={cx('integrationsList')}>
                <WithPermissionControl userAction={UserAction.UpdateAlertReceiveChannels}>
                  <Button
                    onClick={() => {
                      this.setState({ showCreateIntegrationModal: true });
                    }}
                    icon="plus"
                    className={cx('newIntegrationButton')}
                  >
                    New integration for receiving alerts
                  </Button>
                </WithPermissionControl>
                <div className={cx('alert-receive-channels-list')}>
                  <GList
                    autoScroll
                    selectedId={store.selectedAlertReceiveChannel}
                    items={searchResult}
                    itemKey="id"
                    onSelect={this.handleAlertReceiveChannelSelect}
                  >
                    {(item) => (
                      <AlertReceiveChannelCard
                        id={item.id}
                        onShowHeartbeatModal={() => {
                          this.setState({
                            alertReceiveChannelToShowSettings: item.id,
                            integrationSettingsTab: IntegrationSettingsTab.Heartbeat,
                          });
                        }}
                      />
                    )}
                  </GList>
                </div>
              </div>
              <div className={cx('alert-rules', 'alertRulesBorder')}>
                <AlertRules
                  alertReceiveChannelId={store.selectedAlertReceiveChannel}
                  onDelete={this.handleDeleteAlertReceiveChannel}
                  onShowSettings={(integrationSettingsTab?: IntegrationSettingsTab) => {
                    this.setState({
                      alertReceiveChannelToShowSettings: store.selectedAlertReceiveChannel,
                      integrationSettingsTab,
                    });
                  }}
                  /*onEditAlertReceiveChannelTemplates={this.getShowAlertReceiveChannelSettingsClickHandler(
                  store.selectedAlertReceiveChannel
                )}*/
                />
              </div>
            </div>
          ) : searchResult ? (
            <Tutorial
              step={TutorialStep.Integrations}
              title={
                <VerticalGroup align="center" spacing="lg">
                  <Text type="secondary">No integrations found. Review your filter and team settings.</Text>
                  <WithPermissionControl userAction={UserAction.UpdateAlertReceiveChannels}>
                    <Button
                      icon="plus"
                      variant="primary"
                      size="lg"
                      onClick={() => {
                        this.setState({ showCreateIntegrationModal: true });
                      }}
                    >
                      New integration for receiving alerts
                    </Button>
                  </WithPermissionControl>
                </VerticalGroup>
              }
            />
          ) : (
            <LoadingPlaceholder text="Loading..." />
          )}
        </div>
        {alertReceiveChannelToShowSettings && (
          <IntegrationSettings
            onUpdate={() => {
              alertReceiveChannelStore.updateItem(alertReceiveChannelToShowSettings);
            }}
            startTab={integrationSettingsTab}
            id={alertReceiveChannelToShowSettings}
            onHide={() => {
              this.setState({
                alertReceiveChannelToShowSettings: undefined,
                integrationSettingsTab: undefined,
              });
              getLocationSrv().update({ partial: true, query: { tab: undefined } });
            }}
          />
        )}
        {showCreateIntegrationModal && (
          <CreateAlertReceiveChannelContainer
            onHide={() => {
              this.setState({ showCreateIntegrationModal: false });
            }}
            onCreate={this.handleCreateNewAlertReceiveChannel}
          />
        )}
      </>
    );
  }

  handleCreateNewAlertReceiveChannel = (option: AlertReceiveChannelOption) => {
    const { store } = this.props;

    store.alertReceiveChannelStore
      .create({ integration: option.value })
      .then(async (alertReceiveChannel: AlertReceiveChannel) => {
        await store.alertReceiveChannelStore.updateItems();

        this.setSelectedAlertReceiveChannel(alertReceiveChannel.id);

        this.setState({
          alertReceiveChannelToShowSettings: alertReceiveChannel.id,
          integrationSettingsTab: IntegrationSettingsTab.HowToConnect,
        });

        const integration = store.alertReceiveChannelStore.getIntegration(alertReceiveChannel);
        if (integration?.display_name === 'Grafana Alerting') {
          this.alertReceiveChanneltoPoll = { ...this.alertReceiveChanneltoPoll, [alertReceiveChannel.id]: 200 };
          if (!this.alertReceiveChannelTimerId) {
            let counter = 200;
            this.alertReceiveChannelTimerId = setInterval(this.checkTimerTick, 3000);
          }
        }
      });
  };

  checkTimerTick = () => {
    const { store } = this.props;

    if (store.selectedAlertReceiveChannel in this.alertReceiveChanneltoPoll) {
      let counter = this.alertReceiveChanneltoPoll[store.selectedAlertReceiveChannel];
      if (counter > 0) {
        store.alertReceiveChannelStore.updateItem(store.selectedAlertReceiveChannel);
        this.alertReceiveChanneltoPoll[store.selectedAlertReceiveChannel]--;
      } else {
        delete this.alertReceiveChanneltoPoll[store.selectedAlertReceiveChannel];
      }
    }
  };

  handleDeleteAlertReceiveChannel = (alertReceiveChannelId: AlertReceiveChannel['id']) => {
    const { store } = this.props;
    const { alertReceiveChanneltoPoll } = this;

    const { alertReceiveChannelStore } = store;

    if (alertReceiveChanneltoPoll[alertReceiveChannelId]) {
      delete alertReceiveChanneltoPoll[alertReceiveChannelId];
    }

    alertReceiveChannelStore.deleteAlertReceiveChannel(alertReceiveChannelId).then(async () => {
      await alertReceiveChannelStore.updateItems();

      if (alertReceiveChannelId === store.selectedAlertReceiveChannel) {
        const searchResult = alertReceiveChannelStore.getSearchResult();

        this.setSelectedAlertReceiveChannel(searchResult && searchResult[0]?.id);
      }
    });
  };

  applyFilters = () => {
    const { store } = this.props;
    const { alertReceiveChannelStore } = store;
    const { integrationsFilters } = this.state;

    alertReceiveChannelStore.updateItems(integrationsFilters.searchTerm).then(() => {
      const searchResult = alertReceiveChannelStore.getSearchResult();

      if (
        !searchResult.find(
          (alertReceiveChannel: AlertReceiveChannel) => alertReceiveChannel.id === store.selectedAlertReceiveChannel
        )
      ) {
        store.selectedAlertReceiveChannel = searchResult.length ? searchResult[0].id : undefined;
      }
    });
  };

  debouncedUpdateIntegrations = debounce(this.applyFilters, 1000);

  handleIntegrationsFiltersChange = (integrationsFilters: Filters) => {
    this.setState({ integrationsFilters }, this.debouncedUpdateIntegrations);
  };

  handleAlertReceiveChannelSelect = (id: AlertReceiveChannel['id']) => {
    this.setSelectedAlertReceiveChannel(id);
  };
}

export default withMobXProviderContext(Integrations);
