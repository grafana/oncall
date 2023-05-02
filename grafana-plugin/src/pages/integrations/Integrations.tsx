import React from 'react';

import { Button, LoadingPlaceholder, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import qs from 'query-string';
import { RouteComponentProps, withRouter } from 'react-router-dom';

import GList from 'components/GList/GList';
import { Filters } from 'components/IntegrationsFilters/IntegrationsFilters';
import PageErrorHandlingWrapper, { PageBaseState } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper';
import {
  getWrongTeamResponseInfo,
  initErrorDataState,
} from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper.helpers';
import Text from 'components/Text/Text';
import Tutorial from 'components/Tutorial/Tutorial';
import { TutorialStep } from 'components/Tutorial/Tutorial.types';
import AlertReceiveChannelCard from 'containers/AlertReceiveChannelCard/AlertReceiveChannelCard';
import AlertRules from 'containers/AlertRules/AlertRules';
import CreateAlertReceiveChannelContainer from 'containers/CreateAlertReceiveChannelContainer/CreateAlertReceiveChannelContainer';
import IntegrationSettings from 'containers/IntegrationSettings/IntegrationSettings';
import { IntegrationSettingsTab } from 'containers/IntegrationSettings/IntegrationSettings.types';
import RemoteFilters from 'containers/RemoteFilters/RemoteFilters';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import {
  AlertReceiveChannel,
  AlertReceiveChannelOption,
} from 'models/alert_receive_channel/alert_receive_channel.types';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
import { PageProps, WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import LocationHelper from 'utils/LocationHelper';
import { UserActions } from 'utils/authorization';
import { PLUGIN_ROOT } from 'utils/consts';

import styles from './Integrations.module.css';

const cx = cn.bind(styles);

interface IntegrationsState extends PageBaseState {
  integrationsFilters: Filters;
  showCreateIntegrationModal: boolean;
  alertReceiveChannelToShowSettings?: AlertReceiveChannel['id'];
  integrationSettingsTab?: IntegrationSettingsTab;
  extraAlertReceiveChannels?: AlertReceiveChannel[];
}

interface IntegrationsProps extends WithStoreProps, PageProps, RouteComponentProps<{ id: string }> {}

@observer
class Integrations extends React.Component<IntegrationsProps, IntegrationsState> {
  state: IntegrationsState = {
    integrationsFilters: { searchTerm: '' },
    showCreateIntegrationModal: false,
    errorData: initErrorDataState(),
  };

  private alertReceiveChanneltoPoll: { [key: string]: number } = {};
  private alertReceiveChannelTimerId: ReturnType<typeof setTimeout>;

  componentWillUnmount() {
    clearInterval(this.alertReceiveChannelTimerId);
  }

  componentDidUpdate(prevProps: Readonly<IntegrationsProps>): void {
    if (prevProps.match.params.id !== this.props.match.params.id) {
      this.parseQueryParams();
    }
  }

  setSelectedAlertReceiveChannel = (alertReceiveChannelId: AlertReceiveChannel['id']) => {
    const { store } = this.props;
    store.selectedAlertReceiveChannel = alertReceiveChannelId;
  };

  parseQueryParams = async () => {
    this.setState({ errorData: initErrorDataState() }); // reset wrong team error to false on query parse // reset wrong team error to false

    const {
      store,
      query,
      match: {
        params: { id },
      },
    } = this.props;
    const { alertReceiveChannelStore } = store;

    let selectedAlertReceiveChannel = undefined;

    if (id) {
      let alertReceiveChannel = await alertReceiveChannelStore
        .loadItem(id, true)
        .catch((error) => this.setState({ errorData: { ...getWrongTeamResponseInfo(error) } }));

      if (!alertReceiveChannel) {
        return;
      }

      alertReceiveChannel = alertReceiveChannelStore.items[id];
      if (alertReceiveChannel) {
        selectedAlertReceiveChannel = alertReceiveChannel.id;
      }

      if (query.tab) {
        this.setState({ integrationSettingsTab: query.tab });
        this.setState({ alertReceiveChannelToShowSettings: id });
      }
    }

    if (selectedAlertReceiveChannel) {
      this.enrichAlertReceiveChannelsAndSelect(selectedAlertReceiveChannel);
    } else {
      store.selectedAlertReceiveChannel = undefined;
    }
  };

  render() {
    const {
      store,
      match: {
        params: { id },
      },
      query,
    } = this.props;
    const {
      alertReceiveChannelToShowSettings,
      integrationSettingsTab,
      showCreateIntegrationModal,
      errorData,
      extraAlertReceiveChannels,
    } = this.state;

    const { alertReceiveChannelStore, selectedAlertReceiveChannel } = store;

    const searchResult = alertReceiveChannelStore.getSearchResult();

    let data = searchResult.results;
    if (extraAlertReceiveChannels && extraAlertReceiveChannels.length) {
      data = [...extraAlertReceiveChannels, ...searchResult.results];
    }

    return (
      <PageErrorHandlingWrapper
        errorData={errorData}
        objectName="integration"
        pageName="integrations"
        itemNotFoundMessage={`Integration with id=${id} is not found. Please select integration from the list.`}
      >
        {() => (
          <>
            <div className={cx('root')}>
              <div className={cx('filters')}>
                <RemoteFilters
                  query={query}
                  page="integrations"
                  grafanaTeamStore={store.grafanaTeamStore}
                  onChange={this.handleIntegrationsFiltersChange}
                />
              </div>
              {data?.length ? (
                <div className={cx('integrations')}>
                  <div className={cx('integrationsList')}>
                    <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
                      <Button
                        onClick={() => {
                          this.setState({ showCreateIntegrationModal: true });
                        }}
                        icon="plus"
                        className={cx('newIntegrationButton')}
                      >
                        New integration to receive alerts
                      </Button>
                    </WithPermissionControlTooltip>
                    <div className={cx('alert-receive-channels-list')}>
                      <GList
                        autoScroll
                        selectedId={selectedAlertReceiveChannel}
                        items={data}
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

                        LocationHelper.update({ tab: integrationSettingsTab }, 'partial');
                      }}
                    />
                  </div>
                </div>
              ) : data ? (
                <Tutorial
                  step={TutorialStep.Integrations}
                  title={
                    <VerticalGroup align="center" spacing="lg">
                      <Text type="secondary">No integrations found. Review your filter and team settings.</Text>
                      <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
                        <Button
                          icon="plus"
                          variant="primary"
                          size="lg"
                          onClick={() => {
                            this.setState({ showCreateIntegrationModal: true });
                          }}
                        >
                          New integration to receive alerts
                        </Button>
                      </WithPermissionControlTooltip>
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
                  LocationHelper.update({ tab: undefined }, 'partial');
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
        )}
      </PageErrorHandlingWrapper>
    );
  }

  handleCreateNewAlertReceiveChannel = (option: AlertReceiveChannelOption, team: GrafanaTeam['id']) => {
    const { store, history } = this.props;

    store.alertReceiveChannelStore
      .create({ integration: option.value, team })
      .then(async (alertReceiveChannel: AlertReceiveChannel) => {
        await this.applyFilters();

        const query = { ...qs.parse(window.location.search), tab: IntegrationSettingsTab.HowToConnect };

        history.push(`${PLUGIN_ROOT}/integrations/${alertReceiveChannel.id}?${qs.stringify(query)}`);

        const integration = store.alertReceiveChannelStore.getIntegration(alertReceiveChannel);
        if (integration?.display_name === 'Grafana Alerting') {
          this.alertReceiveChanneltoPoll = { ...this.alertReceiveChanneltoPoll, [alertReceiveChannel.id]: 200 };
          if (!this.alertReceiveChannelTimerId) {
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
    const { store, history } = this.props;
    const { extraAlertReceiveChannels } = this.state;
    const { alertReceiveChanneltoPoll } = this;

    const { alertReceiveChannelStore } = store;

    if (alertReceiveChanneltoPoll[alertReceiveChannelId]) {
      delete alertReceiveChanneltoPoll[alertReceiveChannelId];
    }

    alertReceiveChannelStore
      .deleteAlertReceiveChannel(alertReceiveChannelId)
      .then(this.applyFilters)
      .then(() => {
        if (alertReceiveChannelId === store.selectedAlertReceiveChannel) {
          if (extraAlertReceiveChannels) {
            const newExtraAlertReceiveChannels = extraAlertReceiveChannels.filter(
              (alertReceiveChannel) => alertReceiveChannel.id !== alertReceiveChannelId
            );

            this.setState({ extraAlertReceiveChannels: newExtraAlertReceiveChannels });
          }

          const searchResult = alertReceiveChannelStore.getSearchResult();

          const index = searchResult.results.findIndex(
            (alertReceiveChannel: AlertReceiveChannel) => alertReceiveChannel.id === store.selectedAlertReceiveChannel
          );
          const newSelected = searchResult[index - 1] || searchResult[0];

          history.push(`${PLUGIN_ROOT}/integrations/${newSelected?.id || ''}${window.location.search}`);
        }
      });
  };

  applyFilters = () => {
    const { store } = this.props;
    const { alertReceiveChannelStore } = store;
    const { integrationsFilters } = this.state;

    return alertReceiveChannelStore.updateItems(integrationsFilters);
  };

  autoSelectAlertReceiveChannel = () => {
    const { store, history } = this.props;
    const { alertReceiveChannelStore } = store;
    const searchResult = alertReceiveChannelStore.getSearchResult();

    if (
      !searchResult.results?.some(
        (alertReceiveChannel: AlertReceiveChannel) => alertReceiveChannel.id === store.selectedAlertReceiveChannel
      )
    ) {
      const id = searchResult[0]?.id;
      history.push(`${PLUGIN_ROOT}/integrations/${id || ''}${window.location.search}`);
    }
  };

  handleIntegrationsFiltersChange = (integrationsFilters: Filters, isOnMount: boolean) => {
    const {
      match: {
        params: { id },
      },
    } = this.props;

    this.setState({ integrationsFilters, extraAlertReceiveChannels: undefined }, () => {
      this.applyFilters().then(() => {
        if (isOnMount && id) {
          this.parseQueryParams();
        } else {
          this.autoSelectAlertReceiveChannel();
        }
      });
    });
  };

  handleAlertReceiveChannelSelect = (id: AlertReceiveChannel['id']) => {
    const { history } = this.props;

    history.push(`${PLUGIN_ROOT}/integrations/${id}${window.location.search}`);
  };

  enrichAlertReceiveChannelsAndSelect = async (id: AlertReceiveChannel['id']) => {
    const { store } = this.props;
    const { extraAlertReceiveChannels } = this.state;
    const { alertReceiveChannelStore } = store;

    const searchResult = alertReceiveChannelStore.getSearchResult();
    if (
      !searchResult.results.some((alertReceiveChannel) => alertReceiveChannel.id === id) &&
      (!extraAlertReceiveChannels ||
        (extraAlertReceiveChannels &&
          !extraAlertReceiveChannels.some((alertReceiveChannel) => alertReceiveChannel.id === id)))
    ) {
      let alertReceiveChannel = await alertReceiveChannelStore
        .loadItem(id, true)
        .catch((error) => this.setState({ errorData: { ...getWrongTeamResponseInfo(error) } }));

      if (alertReceiveChannel) {
        this.setState(
          { extraAlertReceiveChannels: [...(this.state.extraAlertReceiveChannels || []), alertReceiveChannel] },
          () => {
            this.setSelectedAlertReceiveChannel(id);
          }
        );
      }
    } else {
      this.setSelectedAlertReceiveChannel(id);
    }
  };
}

export default withRouter(withMobXProviderContext(Integrations));
