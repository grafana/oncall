import React from 'react';

import { Button, HorizontalGroup, Icon, IconButton, LoadingPlaceholder, Tooltip, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { debounce } from 'lodash-es';
import { observer } from 'mobx-react';
import { RouteComponentProps, withRouter } from 'react-router-dom';

import Collapse from 'components/Collapse/Collapse';
import EscalationsFilters from 'components/EscalationsFilters/EscalationsFilters';
import Block from 'components/GBlock/Block';
import GList from 'components/GList/GList';
import PageErrorHandlingWrapper, { PageBaseState } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper';
import {
  getWrongTeamResponseInfo,
  initErrorDataState,
} from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper.helpers';
import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import Tutorial from 'components/Tutorial/Tutorial';
import { TutorialStep } from 'components/Tutorial/Tutorial.types';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import EscalationChainCard from 'containers/EscalationChainCard/EscalationChainCard';
import EscalationChainForm from 'containers/EscalationChainForm/EscalationChainForm';
import EscalationChainSteps from 'containers/EscalationChainSteps/EscalationChainSteps';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { EscalationChain } from 'models/escalation_chain/escalation_chain.types';
import { PageProps, WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import { UserActions } from 'utils/authorization';
import { PLUGIN_ROOT } from 'utils/consts';

import styles from './EscalationChains.module.css';

const cx = cn.bind(styles);

interface EscalationChainsPageProps extends WithStoreProps, PageProps, RouteComponentProps<{ id: string }> {}

interface EscalationChainsPageState extends PageBaseState {
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
    errorData: initErrorDataState(),
  };

  async componentDidMount() {
    this.update().then(this.parseQueryParams);
  }

  parseQueryParams = async () => {
    this.setState({ errorData: initErrorDataState() }); // reset on query parse

    const {
      store,
      match: {
        params: { id },
      },
    } = this.props;
    const { escalationChainStore } = store;
    const {
      escalationChainsFilters: { searchTerm },
    } = this.state;

    const searchResult = escalationChainStore.getSearchResult(searchTerm);

    let selectedEscalationChain: EscalationChain['id'];
    if (id) {
      let escalationChain = await escalationChainStore
        .loadItem(id, true)
        .catch((error) => this.setState({ errorData: { ...getWrongTeamResponseInfo(error) } }));

      if (!escalationChain) {
        return;
      }

      escalationChain = escalationChainStore.items[id];
      if (escalationChain) {
        selectedEscalationChain = escalationChain.id;
      }
    }

    if (!selectedEscalationChain) {
      selectedEscalationChain = searchResult[0]?.id;
    }

    if (selectedEscalationChain) {
      this.setSelectedEscalationChain(selectedEscalationChain);
    }
  };

  setSelectedEscalationChain = (escalationChain: EscalationChain['id']) => {
    const { store, history } = this.props;

    const { escalationChainStore } = store;

    this.setState({ selectedEscalationChain: escalationChain }, () => {
      history.push(`${PLUGIN_ROOT}/escalations/${escalationChain || ''}`);
      if (escalationChain) {
        escalationChainStore.updateEscalationChainDetails(escalationChain);
      }
    });
  };

  update = () => {
    const { store } = this.props;

    return store.escalationChainStore.updateItems('');
  };

  componentDidUpdate(prevProps: EscalationChainsPageProps) {
    if (this.props.match.params.id !== prevProps.match.params.id) {
      this.parseQueryParams();
    }
  }

  render() {
    const {
      store,
      match: {
        params: { id },
      },
    } = this.props;
    const {
      showCreateEscalationChainModal,
      escalationChainIdToCopy,
      escalationChainsFilters,
      selectedEscalationChain,
      errorData,
    } = this.state;

    const { escalationChainStore } = store;
    const { loading } = escalationChainStore;
    const searchResult = escalationChainStore.getSearchResult(escalationChainsFilters.searchTerm);

    return (
      <PageErrorHandlingWrapper
        errorData={errorData}
        objectName="escalation"
        pageName="escalations"
        itemNotFoundMessage={`Escalation chain with id=${id} is not found. Please select escalation chain from the list.`}
      >
        {() => (
          <>
            <div className={cx('root')}>
              <div className={cx('filters')}>
                <EscalationsFilters value={escalationChainsFilters} onChange={this.handleEscalationsFiltersChange} />
              </div>
              {!searchResult || searchResult.length ? (
                <div className={cx('escalations')}>
                  <div className={cx('left-column')}>
                    {!loading && (
                      <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
                        <Button
                          onClick={() => {
                            this.setState({ showCreateEscalationChainModal: true });
                          }}
                          icon="plus"
                          className={cx('new-escalation-chain')}
                        >
                          New Escalation Chain
                        </Button>
                      </WithPermissionControlTooltip>
                    )}
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
                      <WithPermissionControlTooltip userAction={UserActions.EscalationChainsWrite}>
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
                      </WithPermissionControlTooltip>
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
        )}
      </PageErrorHandlingWrapper>
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
    const { selectedEscalationChain } = this.state;

    const { escalationChainStore } = store;

    if (!selectedEscalationChain) {
      return null;
    }

    const escalationChain = escalationChainStore.items[selectedEscalationChain];
    const escalationChainDetails = escalationChainStore.details[selectedEscalationChain];

    return (
      <>
        <Block withBackground className={cx('header')}>
          <Text size="large" editable onTextChange={this.handleEscalationChainNameChange}>
            {escalationChain.name}
          </Text>
          <div className={cx('buttons')}>
            <HorizontalGroup>
              <WithPermissionControlTooltip userAction={UserActions.EscalationChainsWrite}>
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
              </WithPermissionControlTooltip>
              <WithPermissionControlTooltip userAction={UserActions.EscalationChainsWrite}>
                <WithConfirm title={`Are you sure to remove "${escalationChain.name}"?`} confirmText="Remove">
                  <IconButton
                    disabled={escalationChain.number_of_integrations > 0}
                    tooltip="Remove"
                    tooltipPlacement="top"
                    onClick={this.handleDeleteEscalationChain}
                    name="trash-alt"
                  />
                </WithConfirm>
              </WithPermissionControlTooltip>
              {escalationChain.number_of_integrations > 0 && (
                <Tooltip content="Escalation chains linked to multiple integrations cannot be removed">
                  <Icon name="info-circle" />
                </Tooltip>
              )}
            </HorizontalGroup>
          </div>
        </Block>
        <EscalationChainSteps id={selectedEscalationChain} />
        {escalationChainDetails ? (
          <Collapse
            headerWithBackground
            label={`${escalationChainDetails.length ? escalationChainDetails.length : 'No'} linked integration${
              escalationChainDetails.length === 1 ? '' : 's'
            } will be affected by changes`}
            isOpen
          >
            {escalationChainDetails.length ? (
              <ul className={cx('list')}>
                {escalationChainDetails.map((alertReceiveChannel) => (
                  <li key={alertReceiveChannel.id}>
                    <HorizontalGroup align="flex-start">
                      <PluginLink query={{ page: 'integrations', id: alertReceiveChannel.id }}>
                        {alertReceiveChannel.display_name}
                      </PluginLink>
                      <ul className={cx('list')}>
                        {alertReceiveChannel.channel_filters.map((channelFilter) => (
                          <li key={channelFilter.id}>
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

export default withRouter(withMobXProviderContext(EscalationChainsPage));
