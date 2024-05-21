import React from 'react';

import { GrafanaTheme2 } from '@grafana/data';
import { Button, HorizontalGroup, Icon, IconButton, Tooltip, VerticalGroup, withTheme2 } from '@grafana/ui';
import { observer } from 'mobx-react';
import { RouteComponentProps, withRouter } from 'react-router-dom';
import { getUtilStyles } from 'styles/utils.styles';

import { Collapse } from 'components/Collapse/Collapse';
import { Block } from 'components/GBlock/Block';
import { GList } from 'components/GList/GList';
import { PageErrorHandlingWrapper, PageBaseState } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper';
import {
  getWrongTeamResponseInfo,
  initErrorDataState,
} from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper.helpers';
import { PluginLink } from 'components/PluginLink/PluginLink';
import { Text } from 'components/Text/Text';
import { Tutorial } from 'components/Tutorial/Tutorial';
import { TutorialStep } from 'components/Tutorial/Tutorial.types';
import { WithConfirm } from 'components/WithConfirm/WithConfirm';
import { EscalationChainCard } from 'containers/EscalationChainCard/EscalationChainCard';
import { EscalationChainForm, EscalationChainFormMode } from 'containers/EscalationChainForm/EscalationChainForm';
import { EscalationChainSteps } from 'containers/EscalationChainSteps/EscalationChainSteps';
import { RemoteFilters } from 'containers/RemoteFilters/RemoteFilters';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { EscalationChain } from 'models/escalation_chain/escalation_chain.types';
import { FiltersValues } from 'models/filters/filters.types';
import { PageProps, WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import { UserActions } from 'utils/authorization/authorization';
import { PAGE, PLUGIN_ROOT } from 'utils/consts';

import { getEscalationChainStyles } from './EscalationChains.styles';

interface EscalationChainsPageProps extends WithStoreProps, PageProps, RouteComponentProps<{ id: string }> {
  theme: GrafanaTheme2;
}

interface EscalationChainsPageState extends PageBaseState {
  modeToShowEscalationChainForm?: EscalationChainFormMode;
  selectedEscalationChain: EscalationChain['id'];
  escalationChainsFilters?: FiltersValues;
  extraEscalationChains?: EscalationChain[]; // to render Escalation chains that are not present in searchResult due to filters
}

export interface Filters {
  searchTerm: string;
}

@observer
class _EscalationChainsPage extends React.Component<EscalationChainsPageProps, EscalationChainsPageState> {
  state: EscalationChainsPageState = {
    selectedEscalationChain: undefined,
    errorData: initErrorDataState(),
  };

  parseQueryParams = async () => {
    this.setState({ errorData: initErrorDataState() }); // reset on query parse

    const {
      store,
      match: {
        params: { id },
      },
    } = this.props;

    const { escalationChainStore } = store;

    let selectedEscalationChain: EscalationChain['id'];

    if (id === 'new') {
      this.setState({
        modeToShowEscalationChainForm: EscalationChainFormMode.Create,
      });
    } else if (id) {
      let escalationChain: EscalationChain;

      try {
        escalationChain = await escalationChainStore.loadItem(id, true);
      } catch (error) {
        this.setState({ errorData: { ...getWrongTeamResponseInfo(error) } });
      }

      await escalationChainStore.updateEscalationChainDetails(id);
      if (!escalationChain) {
        return;
      }

      escalationChain = escalationChainStore.items[id];
      if (escalationChain) {
        selectedEscalationChain = escalationChain.id;
      }
    }

    if (selectedEscalationChain) {
      this.enrichExtraEscalationChainsAndSelect(selectedEscalationChain);
    } else {
      this.setState({ selectedEscalationChain: undefined });
    }
  };

  handleEsclalationSelect = (id: EscalationChain['id']) => {
    const { history } = this.props;

    history.push(`${PLUGIN_ROOT}/escalations/${id}${window.location.search}`);
  };

  setSelectedEscalationChain = async (escalationChainId: EscalationChain['id']) => {
    const { store } = this.props;

    const { escalationChainStore } = store;

    this.setState({ selectedEscalationChain: escalationChainId }, () => {
      if (escalationChainId) {
        escalationChainStore.updateEscalationChainDetails(escalationChainId);
      }
    });
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
      theme,
    } = this.props;

    const { extraEscalationChains } = this.state;

    const { modeToShowEscalationChainForm, selectedEscalationChain, errorData } = this.state;

    const { escalationChainStore } = store;
    const searchResult = escalationChainStore.getSearchResult();

    let data = searchResult;
    if (extraEscalationChains && extraEscalationChains.length) {
      data = [...extraEscalationChains, ...searchResult];
    }

    const styles = getEscalationChainStyles(theme);
    const utilStyles = getUtilStyles(theme);

    return (
      <PageErrorHandlingWrapper
        errorData={errorData}
        objectName="escalation"
        pageName="escalations"
        itemNotFoundMessage={`Escalation chain with id=${id} is not found. Please select escalation chain from the list.`}
      >
        {() => (
          <>
            <div>
              {this.renderFilters()}
              {!data || data.length ? (
                <div className={styles.escalations}>
                  <div className={styles.leftColumn}>
                    <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
                      <Button
                        onClick={() => {
                          this.setState({ modeToShowEscalationChainForm: EscalationChainFormMode.Create });
                        }}
                        icon="plus"
                        className={styles.newEscalationChain}
                      >
                        New escalation chain
                      </Button>
                    </WithPermissionControlTooltip>
                    <div className={styles.escalationsList} data-testid="escalation-chains-list">
                      {data ? (
                        <GList
                          autoScroll
                          selectedId={selectedEscalationChain}
                          items={data}
                          itemKey="id"
                          onSelect={this.handleEsclalationSelect}
                        >
                          {(item) => <EscalationChainCard id={item.id} />}
                        </GList>
                      ) : (
                        <VerticalGroup>
                          <Text type="primary" className={utilStyles.loadingPlaceholder}>
                            Loading...
                          </Text>
                        </VerticalGroup>
                      )}
                    </div>
                  </div>
                  <div className={styles.escalation}>{this.renderEscalation()}</div>
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
                            this.setState({ modeToShowEscalationChainForm: EscalationChainFormMode.Create });
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
            {modeToShowEscalationChainForm && (
              <EscalationChainForm
                mode={modeToShowEscalationChainForm}
                escalationChainId={
                  modeToShowEscalationChainForm === EscalationChainFormMode.Create ? undefined : selectedEscalationChain
                }
                onHide={() => {
                  this.setState({
                    modeToShowEscalationChainForm: undefined,
                  });
                }}
                onSubmit={this.handleEscalationChainCreate}
              />
            )}
          </>
        )}
      </PageErrorHandlingWrapper>
    );
  }

  renderFilters() {
    const { query, store, theme } = this.props;
    const styles = getEscalationChainStyles(theme);

    return (
      <div className={styles.filters}>
        <RemoteFilters
          query={query}
          page={PAGE.Escalations}
          grafanaTeamStore={store.grafanaTeamStore}
          onChange={this.handleFiltersChange}
        />
      </div>
    );
  }

  handleFiltersChange = (filters: FiltersValues, isOnMount = false) => {
    const {
      match: {
        params: { id },
      },
    } = this.props;

    this.setState({ escalationChainsFilters: filters, extraEscalationChains: undefined }, async () => {
      await this.applyFilters();
      if (isOnMount && id) {
        this.parseQueryParams();
      } else {
        this.autoSelectEscalationChain();
      }
    });
  };

  autoSelectEscalationChain = () => {
    const { store, history } = this.props;
    const { selectedEscalationChain } = this.state;
    const { escalationChainStore } = store;

    const searchResult = escalationChainStore.getSearchResult();

    if (!searchResult.find((escalationChain: EscalationChain) => escalationChain.id === selectedEscalationChain)) {
      const id = searchResult[0]?.id;
      history.push(`${PLUGIN_ROOT}/escalations/${id || ''}${window.location.search}`);
    }
  };

  applyFilters = () => {
    const { store } = this.props;
    const { escalationChainStore } = store;
    const { escalationChainsFilters } = this.state;

    return escalationChainStore.updateItems(escalationChainsFilters);
  };

  renderEscalation = () => {
    const { store, theme } = this.props;
    const { selectedEscalationChain } = this.state;

    const { escalationChainStore } = store;

    if (!selectedEscalationChain) {
      return null;
    }

    const escalationChain = escalationChainStore.items[selectedEscalationChain];
    const escalationChainDetails = escalationChainStore.details[selectedEscalationChain];
    const styles = getEscalationChainStyles(theme);

    return (
      <>
        <Block withBackground className={styles.header}>
          <Text size="large" onTextChange={this.handleEscalationChainNameChange} data-testid="escalation-chain-name">
            {escalationChain.name}
          </Text>
          <div className={styles.buttons}>
            <HorizontalGroup>
              <WithPermissionControlTooltip userAction={UserActions.EscalationChainsWrite}>
                <IconButton
                  tooltip="Edit"
                  tooltipPlacement="top"
                  name="cog"
                  onClick={() => {
                    this.setState({
                      modeToShowEscalationChainForm: EscalationChainFormMode.Update,
                    });
                  }}
                />
              </WithPermissionControlTooltip>
              <WithPermissionControlTooltip userAction={UserActions.EscalationChainsWrite}>
                <IconButton
                  tooltip="Copy"
                  tooltipPlacement="top"
                  name="copy"
                  onClick={() => {
                    this.setState({
                      modeToShowEscalationChainForm: EscalationChainFormMode.Copy,
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
              <ul className={styles.list}>
                {escalationChainDetails.map((alertReceiveChannel) => (
                  <li key={alertReceiveChannel.id}>
                    <HorizontalGroup align="flex-start">
                      <PluginLink query={{ page: 'integrations', id: alertReceiveChannel.id }}>
                        {alertReceiveChannel.display_name}
                      </PluginLink>
                      <ul className={styles.list}>
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

  handleEscalationChainCreate = async (id: EscalationChain['id']) => {
    const { selectedEscalationChain } = this.state;
    const { history } = this.props;

    await this.applyFilters();

    history.push(`${PLUGIN_ROOT}/escalations/${id}${window.location.search}`);

    // because this page wouldn't detect query.id change
    if (selectedEscalationChain === id) {
      this.parseQueryParams();
    }
  };

  enrichExtraEscalationChainsAndSelect = async (id: EscalationChain['id']) => {
    const { store } = this.props;
    const { extraEscalationChains } = this.state;
    const { escalationChainStore } = store;

    await this.applyFilters();

    const searchResult = escalationChainStore.getSearchResult();
    if (
      !searchResult.some((escalationChain) => escalationChain.id === id) &&
      (!extraEscalationChains ||
        (extraEscalationChains && !extraEscalationChains.some((escalationChain) => escalationChain.id === id)))
    ) {
      let escalationChain: EscalationChain;

      try {
        escalationChain = await escalationChainStore.loadItem(id, true);
      } catch (error) {
        this.setState({ errorData: { ...getWrongTeamResponseInfo(error) } });
      }

      if (escalationChain) {
        this.setState({ extraEscalationChains: [...(this.state.extraEscalationChains || []), escalationChain] }, () => {
          this.setSelectedEscalationChain(id);
        });
      }
    } else {
      this.setSelectedEscalationChain(id);
    }
  };

  handleDeleteEscalationChain = async () => {
    const { store, history } = this.props;
    const { escalationChainStore } = store;
    const { selectedEscalationChain, extraEscalationChains } = this.state;

    const index = escalationChainStore
      .getSearchResult()
      .findIndex((escalationChain: EscalationChain) => escalationChain.id === selectedEscalationChain);

    await escalationChainStore.delete(selectedEscalationChain);
    await this.applyFilters();

    if (extraEscalationChains) {
      const newExtraEscalationChains = extraEscalationChains.filter(
        (scalationChain) => scalationChain.id !== selectedEscalationChain
      );

      this.setState({ extraEscalationChains: newExtraEscalationChains });
    }

    const escalationChains = escalationChainStore.getSearchResult();

    const newSelected = escalationChains[index - 1] || escalationChains[0];

    history.push(`${PLUGIN_ROOT}/escalations/${newSelected?.id || ''}${window.location.search}`);
  };

  handleEscalationChainNameChange = (value: string) => {
    const { store } = this.props;
    const { selectedEscalationChain } = this.state;

    const { escalationChainStore } = store;

    escalationChainStore.save(selectedEscalationChain, { name: value });
  };
}

export const EscalationChainsPage = withRouter(withMobXProviderContext(withTheme2(_EscalationChainsPage)));
