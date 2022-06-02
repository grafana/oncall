import React from 'react';

import { AppRootProps } from '@grafana/data';
import { getLocationSrv } from '@grafana/runtime';
import {
  Alert,
  Button,
  EmptySearchResult,
  HorizontalGroup,
  Icon,
  IconButton,
  LoadingPlaceholder,
  Tooltip,
  VerticalGroup,
} from '@grafana/ui';
import cn from 'classnames/bind';
import { debounce } from 'lodash-es';
import { observer } from 'mobx-react';

import Collapse from 'components/Collapse/Collapse';
import EscalationsFilters from 'components/EscalationsFilters/EscalationsFilters';
import Block from 'components/GBlock/Block';
import GList from 'components/GList/GList';
import IntegrationsFilters from 'components/IntegrationsFilters/IntegrationsFilters';
import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import Tutorial from 'components/Tutorial/Tutorial';
import { TutorialStep } from 'components/Tutorial/Tutorial.types';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import AlertReceiveChannelCard from 'containers/AlertReceiveChannelCard/AlertReceiveChannelCard';
import EscalationChainCard from 'containers/EscalationChainCard/EscalationChainCard';
import EscalationChainForm from 'containers/EscalationChainForm/EscalationChainForm';
import EscalationChainSteps from 'containers/EscalationChainSteps/EscalationChainSteps';
import GSelect from 'containers/GSelect/GSelect';
import { IntegrationSettingsTab } from 'containers/IntegrationSettings/IntegrationSettings.types';
import { WithPermissionControl } from 'containers/WithPermissionControl/WithPermissionControl';
import { AlertReceiveChannel } from 'models/alert_receive_channel';
import { ChannelFilter } from 'models/channel_filter/channel_filter.types';
import { EscalationChain } from 'models/escalation_chain/escalation_chain.types';
import { SelectOption, WithStoreProps } from 'state/types';
import { UserAction } from 'state/userAction';
import { withMobXProviderContext } from 'state/withStore';
import { openWarningNotification } from 'utils';

import styles from './EscalationChains.module.css';

const cx = cn.bind(styles);

interface EscalationChainsPageProps extends WithStoreProps, AppRootProps {}

interface EscalationChainsPageState {
  escalationChainsFilters: { searchTerm: string };
  showCreateEscalationChainModal: boolean;
  escalationChainIdToCopy: EscalationChain['id'];
  selectedEscalationChain: EscalationChain['id'];
}

export interface Filters {
  searchTerm: string;
}

@observer
class EscalationChainsPage extends React.Component<EscalationChainsPageProps, EscalationChainsPageState> {
  state: EscalationChainsPageState = {
    escalationChainsFilters: { searchTerm: '' },
    showCreateEscalationChainModal: false,
    escalationChainIdToCopy: undefined,
    selectedEscalationChain: undefined,
  };

  async componentDidMount() {
    this.update().then(this.parseQueryParams);
  }

  parseQueryParams = () => {
    const { store, query } = this.props;
    const {
      escalationChainsFilters: { searchTerm },
    } = this.state;

    const { escalationChainStore } = store;

    const searchResult = escalationChainStore.getSearchResult(searchTerm);

    let selectedEscalationChain;
    if (query.id) {
      const escalationChain = escalationChainStore.items[query.id];
      if (escalationChain) {
        selectedEscalationChain = escalationChain.id;
      } else {
        openWarningNotification(
          `Escalation chain with id=${query?.id} is not found. Please select escalation chain from the list.`
        );
      }
    }
    if (!selectedEscalationChain) {
      selectedEscalationChain = searchResult[0]?.id;
    }
    this.setSelectedEscalationChain(selectedEscalationChain);
  };

  setSelectedEscalationChain = (escalationChain: EscalationChain['id']) => {
    const { store } = this.props;

    const { escalationChainStore } = store;

    this.setState({ selectedEscalationChain: escalationChain }, () => {
      getLocationSrv().update({ partial: true, query: { id: escalationChain } });
      if (escalationChain) {
        escalationChainStore.updateEscalationChainDetails(escalationChain);
      }
    });
  };

  update = () => {
    const { store } = this.props;

    return store.escalationChainStore.updateItems();
  };

  componentDidUpdate() {}

  render() {
    const { store } = this.props;
    const {
      showCreateEscalationChainModal,
      escalationChainIdToCopy,
      escalationChainsFilters,
      selectedEscalationChain,
    } = this.state;

    const { escalationChainStore } = store;
    const searchResult = escalationChainStore.getSearchResult(escalationChainsFilters.searchTerm);

    return (
      <>
        <div className={cx('root')}>
          <div className={cx('filters')}>
            <EscalationsFilters value={escalationChainsFilters} onChange={this.handleEscalationsFiltersChange} />
          </div>
          {!searchResult || searchResult.length ? (
            <div className={cx('escalations')}>
              <div className={cx('left-column')}>
                <WithPermissionControl userAction={UserAction.UpdateAlertReceiveChannels}>
                  <Button
                    onClick={() => {
                      this.setState({ showCreateEscalationChainModal: true });
                    }}
                    icon="plus"
                    className={cx('new-escalation-chain')}
                  >
                    New escalation chain
                  </Button>
                </WithPermissionControl>
                <div className={cx('escalations-list')}>
                  {searchResult ? (
                    <GList
                      autoScroll
                      selectedId={selectedEscalationChain}
                      items={searchResult}
                      itemKey="id"
                      onSelect={this.setSelectedEscalationChain}
                    >
                      {(item) => <EscalationChainCard id={item.id} />}
                    </GList>
                  ) : (
                    <LoadingPlaceholder className={cx('loading')} text="Loading..." />
                  )}
                </div>
              </div>
              <div className={cx('escalation')}>{this.renderEscalation()}</div>
            </div>
          ) : (
            <Tutorial
              step={TutorialStep.Escalations}
              title={
                <VerticalGroup align="center" spacing="lg">
                  <Text type="secondary">No escalations found, check your filtering and current team.</Text>
                  <WithPermissionControl userAction={UserAction.UpdateEscalationPolicies}>
                    <Button
                      icon="plus"
                      variant="primary"
                      size="lg"
                      onClick={() => {
                        this.setState({ showCreateEscalationChainModal: true });
                      }}
                    >
                      New Escalation Chain
                    </Button>
                  </WithPermissionControl>
                </VerticalGroup>
              }
            />
          )}
        </div>
        {showCreateEscalationChainModal && (
          <EscalationChainForm
            escalationChainId={escalationChainIdToCopy}
            onHide={() => {
              this.setState({
                showCreateEscalationChainModal: false,
                escalationChainIdToCopy: undefined,
              });
            }}
            onUpdate={this.handleEscalationChainCreate}
          />
        )}
      </>
    );
  }

  applyFilters = () => {
    const { store } = this.props;
    const { escalationChainStore } = store;
    const { escalationChainsFilters, selectedEscalationChain } = this.state;

    escalationChainStore.updateItems(escalationChainsFilters.searchTerm).then(() => {
      const searchResult = escalationChainStore.getSearchResult(escalationChainsFilters.searchTerm);

      if (!searchResult.find((escalationChain: EscalationChain) => escalationChain.id === selectedEscalationChain)) {
        this.setSelectedEscalationChain(searchResult[0].id);
      }
    });
  };

  debouncedUpdateEscalations = debounce(this.applyFilters, 1000);

  handleEscalationsFiltersChange = (filters: Filters) => {
    this.setState({ escalationChainsFilters: filters }, this.debouncedUpdateEscalations);
  };

  renderEscalation = () => {
    const { store } = this.props;
    const { selectedEscalationChain, showCreateEscalationChainModal, escalationChainIdToCopy } = this.state;

    const { escalationChainStore } = store;

    if (!selectedEscalationChain) {
      return null;
    }

    const escalationChain = escalationChainStore.items[selectedEscalationChain];
    const escalationChainDetails = escalationChainStore.details[selectedEscalationChain];

    let warningAboutModifyingEscalationChain = null;
    if (escalationChain.number_of_integrations > 0 || escalationChain.number_of_routes > 0) {
      warningAboutModifyingEscalationChain = (
        <>
          Modifying this escalation chain will affect{' '}
          {escalationChain.number_of_integrations > 0 && (
            <Text strong>
              {escalationChain.number_of_integrations} integration
              {escalationChain.number_of_integrations === 1 ? '' : 's'}
            </Text>
          )}
          {escalationChain.number_of_routes > 0 && escalationChain.number_of_integrations > 0 && ' and '}
          {escalationChain.number_of_routes > 0 && (
            <Text strong>
              {escalationChain.number_of_routes} route{escalationChain.number_of_routes === 1 ? '' : 's'}
            </Text>
          )}
          . Escalation chains linked to multiple integrations cannot be removed.
        </>
      );
    }

    return (
      <>
        <Block withBackground className={cx('header')}>
          <Text size="large" editable onTextChange={this.handleEscalationChainNameChange}>
            {escalationChain.name}
          </Text>
          <div className={cx('buttons')}>
            <HorizontalGroup>
              <WithPermissionControl userAction={UserAction.UpdateEscalationPolicies}>
                <IconButton
                  tooltip="Copy"
                  tooltipPlacement="top"
                  name="copy"
                  onClick={() => {
                    this.setState({
                      showCreateEscalationChainModal: true,
                      escalationChainIdToCopy: selectedEscalationChain,
                    });
                  }}
                />
              </WithPermissionControl>
              <WithPermissionControl userAction={UserAction.UpdateEscalationPolicies}>
                <WithConfirm title={`Are you sure to remove "${escalationChain.name}"?`} confirmText="Remove">
                  <IconButton
                    disabled={escalationChain.number_of_integrations > 1}
                    tooltip="Remove"
                    tooltipPlacement="top"
                    onClick={this.handleDeleteEscalationChain}
                    name="trash-alt"
                  />
                </WithConfirm>
              </WithPermissionControl>
              {escalationChain.number_of_integrations > 1 && (
                <Tooltip content="Escalation chains linked to multiple integrations cannot be removed">
                  <Icon name="info-circle" />
                </Tooltip>
              )}
            </HorizontalGroup>
          </div>
        </Block>
        {warningAboutModifyingEscalationChain && (
          // @ts-ignore
          <Alert title={warningAboutModifyingEscalationChain} severity="warning" />
        )}
        <EscalationChainSteps id={selectedEscalationChain} />
        {escalationChainDetails ? (
          <Collapse
            headerWithBackground
            label={`${escalationChainDetails.length ? escalationChainDetails.length : 'No'} Linked integration${
              escalationChainDetails.length === 1 ? '' : 's'
            }`}
            isOpen
          >
            {escalationChainDetails.length ? (
              <ul className={cx('list')}>
                {escalationChainDetails.map((alertReceiveChannel) => (
                  <li>
                    <HorizontalGroup align="flex-start">
                      <PluginLink query={{ page: 'integrations', id: alertReceiveChannel.id }}>
                        {alertReceiveChannel.display_name}
                      </PluginLink>
                      <ul className={cx('list')}>
                        {alertReceiveChannel.channel_filters.map((channelFilter) => (
                          <li>
                            <Icon name="arrow-right" />
                            {channelFilter.display_name}
                          </li>
                        ))}
                      </ul>
                    </HorizontalGroup>
                  </li>
                ))}
              </ul>
            ) : (
              <Text type="secondary">
                You can link escalation chains to routes on{' '}
                <PluginLink query={{ page: 'integrations' }}>Integrations</PluginLink> page
              </Text>
            )}
          </Collapse>
        ) : null}
      </>
    );
  };

  handleEscalationChainCreate = (id: EscalationChain['id']) => {
    this.update().then(() => {
      this.setSelectedEscalationChain(id);
    });
  };

  handleDeleteEscalationChain = () => {
    const { store } = this.props;
    const { escalationChainStore } = store;
    const { selectedEscalationChain, escalationChainsFilters } = this.state;

    const index = escalationChainStore
      .getSearchResult(escalationChainsFilters.searchTerm)
      .findIndex((escalationChain: EscalationChain) => escalationChain.id === selectedEscalationChain);

    escalationChainStore
      .delete(selectedEscalationChain)
      .then(this.update)
      .then(() => {
        const escalationChains = escalationChainStore.getSearchResult(escalationChainsFilters.searchTerm);

        const newSelected = escalationChains[index - 1] || escalationChains[0];

        this.setSelectedEscalationChain(newSelected?.id);
      });
  };

  handleEscalationChainNameChange = (value: string) => {
    const { store } = this.props;
    const { selectedEscalationChain } = this.state;

    const { escalationChainStore } = store;

    escalationChainStore.save(selectedEscalationChain, { name: value });
  };

  handleEscalationChainSelect = () => {};
}

export default withMobXProviderContext(EscalationChainsPage);
