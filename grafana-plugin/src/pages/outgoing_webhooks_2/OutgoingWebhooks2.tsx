import React from 'react';

import { Button, ConfirmModal, HorizontalGroup, Icon, IconButton, VerticalGroup, WithContextMenu } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import moment from 'moment-timezone';
import LegacyNavHeading from 'navbar/LegacyNavHeading';
import CopyToClipboard from 'react-copy-to-clipboard';
import { RouteComponentProps, withRouter } from 'react-router-dom';

import GTable from 'components/GTable/GTable';
import HamburgerMenu from 'components/HamburgerMenu/HamburgerMenu';
import PageErrorHandlingWrapper, { PageBaseState } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper';
import {
  getWrongTeamResponseInfo,
  initErrorDataState,
} from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper.helpers';
import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import OutgoingWebhook2Form from 'containers/OutgoingWebhook2Form/OutgoingWebhook2Form';
import RemoteFilters from 'containers/RemoteFilters/RemoteFilters';
import TeamName from 'containers/TeamName/TeamName';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { FiltersValues } from 'models/filters/filters.types';
import { OutgoingWebhook } from 'models/outgoing_webhook/outgoing_webhook.types';
import { OutgoingWebhook2 } from 'models/outgoing_webhook_2/outgoing_webhook_2.types';
import { AppFeature } from 'state/features';
import { PageProps, WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import { openErrorNotification, openNotification } from 'utils';
import { isUserActionAllowed, UserActions } from 'utils/authorization';
import { PLUGIN_ROOT } from 'utils/consts';

import styles from './OutgoingWebhooks2.module.scss';
import { WebhookFormActionType } from './OutgoingWebhooks2.types';

const cx = cn.bind(styles);

interface OutgoingWebhooks2Props
  extends WithStoreProps,
    PageProps,
    RouteComponentProps<{ id: string; action: string }> {}

interface OutgoingWebhooks2State extends PageBaseState {
  outgoingWebhook2Action?: WebhookFormActionType;
  outgoingWebhook2Id?: OutgoingWebhook2['id'];
  confirmationModal: {
    isOpen: boolean;
    title: any;
    dismissText: string;
    confirmText: string;
    body?: React.ReactNode;
    description?: string;
    confirmationText?: string;
    onConfirm: () => void;
  };
}

@observer
class OutgoingWebhooks2 extends React.Component<OutgoingWebhooks2Props, OutgoingWebhooks2State> {
  state: OutgoingWebhooks2State = {
    errorData: initErrorDataState(),
    confirmationModal: undefined,
  };

  componentDidUpdate(prevProps: OutgoingWebhooks2Props) {
    if (prevProps.match.params.id !== this.props.match.params.id && !this.state.outgoingWebhook2Action) {
      this.parseQueryParams();
    }
  }

  parseQueryParams = async () => {
    this.setState((_prevState) => ({
      errorData: initErrorDataState(),
      outgoingWebhook2Id: undefined,
    })); // reset state on query parse

    const {
      store,
      match: {
        params: { id, action },
      },
    } = this.props;

    if (action) {
      this.setState({ outgoingWebhook2Id: id, outgoingWebhook2Action: convertWebhookUrlToAction(action) });
    }

    const isNewWebhook = id === 'new';
    if (isNewWebhook) {
      this.setState({ outgoingWebhook2Id: id, outgoingWebhook2Action: WebhookFormActionType.NEW });
    } else if (id) {
      await store.outgoingWebhook2Store
        .loadItem(id, true)
        .catch((error) => this.setState({ errorData: { ...getWrongTeamResponseInfo(error) } }));
    }
  };

  update = () => {
    const { store } = this.props;
    return store.outgoingWebhook2Store.updateItems();
  };

  render() {
    const { store, query } = this.props;
    const { outgoingWebhook2Id, outgoingWebhook2Action, errorData, confirmationModal } = this.state;

    const webhooks = store.outgoingWebhook2Store.getSearchResult();

    const columns = [
      {
        width: '25%',
        title: 'Name',
        dataIndex: 'name',
        render: this.renderName,
      },
      {
        width: '10%',
        title: 'Trigger type',
        dataIndex: 'trigger_type_name',
      },
      {
        width: '35%',
        title: 'URL',
        dataIndex: 'url',
        render: this.renderUrl,
      },
      {
        width: '10%',
        title: 'Last run',
        render: this.renderLastRun,
      },
      {
        width: '15%',
        title: 'Team',
        render: (item: OutgoingWebhook) => this.renderTeam(item, store.grafanaTeamStore.items),
      },
      {
        width: '20%',
        key: 'action',
        render: this.renderActionButtons,
      },
    ];

    return store.hasFeature(AppFeature.Webhooks2) ? (
      <PageErrorHandlingWrapper
        errorData={errorData}
        objectName="outgoing webhook 2"
        pageName="outgoing_webhooks_2"
        itemNotFoundMessage={`Outgoing webhook with id=${query?.id} is not found. Please select outgoing webhook from the list.`}
      >
        {() => (
          <>
            {confirmationModal && (
              <ConfirmModal
                isOpen={confirmationModal.isOpen}
                title={confirmationModal.title}
                confirmText={confirmationModal.confirmText}
                dismissText="Cancel"
                body={confirmationModal.body}
                description={confirmationModal.description}
                confirmationText={confirmationModal.confirmationText}
                onConfirm={confirmationModal.onConfirm}
                onDismiss={() =>
                  this.setState({
                    confirmationModal: undefined,
                  })
                }
              />
            )}

            <div className={cx('root')}>
              {this.renderOutgoingWebhooksFilters()}
              <GTable
                emptyText={webhooks ? 'No outgoing webhooks found' : 'Loading...'}
                title={() => (
                  <div className={cx('header')}>
                    <div className="header__title">
                      <VerticalGroup spacing="sm">
                        <LegacyNavHeading>
                          <Text.Title level={3}>Outgoing Webhooks 2</Text.Title>
                        </LegacyNavHeading>
                        <Text type="secondary" className={cx('header__desc')}>
                          <Icon name="exclamation-triangle"></Icon> Preview Functionality! Things will change and things
                          will break! Do not use for critical production processes!
                        </Text>
                      </VerticalGroup>
                    </div>

                    <div className="u-pull-right">
                      <PluginLink
                        query={{ page: 'outgoing_webhooks_2', id: 'new' }}
                        disabled={!isUserActionAllowed(UserActions.OutgoingWebhooksWrite)}
                      >
                        <WithPermissionControlTooltip userAction={UserActions.OutgoingWebhooksWrite}>
                          <Button variant="primary" icon="plus">
                            Create
                          </Button>
                        </WithPermissionControlTooltip>
                      </PluginLink>
                    </div>
                  </div>
                )}
                rowKey="id"
                columns={columns}
                data={webhooks}
              />
            </div>

            {outgoingWebhook2Id && outgoingWebhook2Action && (
              <OutgoingWebhook2Form
                id={outgoingWebhook2Id}
                action={outgoingWebhook2Action}
                onUpdate={this.update}
                onHide={this.handleOutgoingWebhookFormHide}
              />
            )}
          </>
        )}
      </PageErrorHandlingWrapper>
    ) : (
      <Text>Outgoing webhooks 2 functionality is not enabled.</Text>
    );
  }

  renderOutgoingWebhooksFilters() {
    const { query, store } = this.props;
    return (
      <div className={cx('filters')}>
        <RemoteFilters
          query={query}
          page="webhooks"
          grafanaTeamStore={store.grafanaTeamStore}
          onChange={this.handleFiltersChange}
        />
      </div>
    );
  }

  handleFiltersChange = (filters: FiltersValues, isOnMount) => {
    const { store } = this.props;

    const { outgoingWebhook2Store } = store;

    outgoingWebhook2Store.updateItems(filters).then(() => {
      if (isOnMount) {
        this.parseQueryParams();
      }
    });
  };

  renderTeam(record: OutgoingWebhook, teams: any) {
    return <TeamName team={teams[record.team]} />;
  }

  renderActionButtons = (record: OutgoingWebhook2) => {
    return (
      <WithContextMenu
        renderMenuItems={() => (
          <div className={cx('hamburgerMenu')}>
            <div className={cx('hamburgerMenu__item')} onClick={() => this.onLastRunClick(record.id)}>
              <WithPermissionControlTooltip key={'status_action'} userAction={UserActions.OutgoingWebhooksRead}>
                <Text type="primary">View Last Run</Text>
              </WithPermissionControlTooltip>
            </div>

            <div className={cx('hamburgerMenu__item')} onClick={() => this.onEditClick(record.id)}>
              <WithPermissionControlTooltip key={'edit_action'} userAction={UserActions.OutgoingWebhooksWrite}>
                <Text type="primary">Edit settings</Text>
              </WithPermissionControlTooltip>
            </div>

            <div
              className={cx('hamburgerMenu__item')}
              onClick={() =>
                this.setState({
                  confirmationModal: {
                    isOpen: true,
                    confirmText: 'Confirm',
                    dismissText: 'Cancel',
                    onConfirm: () => this.onDisableWebhook(record.id, !record.is_webhook_enabled),
                    title: `Are you sure you want to ${record.is_webhook_enabled ? 'disable' : 'enable'} ${
                      record.name
                    }?`,
                  },
                })
              }
            >
              <WithPermissionControlTooltip key={'disable_action'} userAction={UserActions.OutgoingWebhooksWrite}>
                <Text type="primary">{record.is_webhook_enabled ? 'Disable' : 'Enable'}</Text>
              </WithPermissionControlTooltip>
            </div>

            <div className={cx('hamburgerMenu__item')} onClick={() => this.onCopyClick(record.id)}>
              <WithPermissionControlTooltip key={'copy_action'} userAction={UserActions.OutgoingWebhooksWrite}>
                <Text type="primary">Make a copy</Text>
              </WithPermissionControlTooltip>
            </div>

            <CopyToClipboard text={record.id}>
              <div className={cx('hamburgerMenu__item')}>
                <HorizontalGroup type="primary" spacing="xs">
                  <Icon name="clipboard-alt" />
                  <Text type="primary">UID: {record.id}</Text>
                </HorizontalGroup>
              </div>
            </CopyToClipboard>

            <div className={cx('thin-line-break')} />

            <div
              className={cx('hamburgerMenu__item')}
              onClick={() =>
                this.setState({
                  confirmationModal: {
                    isOpen: true,
                    confirmText: 'Confirm',
                    dismissText: 'Cancel',
                    onConfirm: () => this.onDeleteClick(record.id),
                    title: `Are you sure you want to delete ${record.name}?`,
                  },
                })
              }
            >
              <WithPermissionControlTooltip key={'delete_action'} userAction={UserActions.OutgoingWebhooksWrite}>
                <HorizontalGroup spacing="xs">
                  <IconButton tooltip="Remove" tooltipPlacement="top" variant="destructive" name="trash-alt" />
                  <Text type="danger">Delete Webhook</Text>
                </HorizontalGroup>
              </WithPermissionControlTooltip>
            </div>
          </div>
        )}
      >
        {({ openMenu }) => <HamburgerMenu openMenu={openMenu} listBorder={2} listWidth={225} withBackground />}
      </WithContextMenu>
    );
  };

  renderName(name: String) {
    return (
      <div className="u-break-word">
        <span>{name}</span>
      </div>
    );
  }

  renderUrl(url: string) {
    return (
      <div className="u-break-word">
        <span>{url}</span>
      </div>
    );
  }

  renderLastRun(record: OutgoingWebhook2) {
    const lastRunMoment = moment(record.last_response_log?.timestamp);

    return !record.is_webhook_enabled ? (
      <Text type="secondary">Disabled</Text>
    ) : (
      <VerticalGroup spacing="none">
        <Text type="secondary">{lastRunMoment.isValid() ? lastRunMoment.format('MMM DD, YYYY') : '-'}</Text>
        <Text type="secondary">{lastRunMoment.isValid() ? lastRunMoment.format('HH:mm') : ''}</Text>
        <Text type="secondary">
          {lastRunMoment.isValid()
            ? record.last_response_log?.status_code
              ? 'Status: ' + record.last_response_log?.status_code
              : 'Check Status'
            : ''}
        </Text>
      </VerticalGroup>
    );
  }

  onDeleteClick = (id: OutgoingWebhook2['id']) => {
    const { store } = this.props;
    return store.outgoingWebhook2Store
      .delete(id)
      .then(this.update)
      .then(() => openNotification('Webhook has been removed'))
      .catch(() => openNotification('Webook could not been removed'))
      .finally(() => this.setState({ confirmationModal: undefined }));
  };

  onEditClick = (id: OutgoingWebhook2['id']) => {
    const { history } = this.props;

    this.setState({ outgoingWebhook2Id: id, outgoingWebhook2Action: WebhookFormActionType.EDIT_SETTINGS }, () =>
      history.push(`${PLUGIN_ROOT}/outgoing_webhooks_2/edit/${id}`)
    );
  };

  onCopyClick = (id: OutgoingWebhook2['id']) => {
    const { history } = this.props;

    this.setState({ outgoingWebhook2Id: id, outgoingWebhook2Action: WebhookFormActionType.COPY }, () =>
      history.push(`${PLUGIN_ROOT}/outgoing_webhooks_2/copy/${id}`)
    );
  };

  onDisableWebhook = (id: OutgoingWebhook2['id'], isEnabled: boolean) => {
    const {
      store: { outgoingWebhook2Store },
    } = this.props;

    const data = {
      ...{ ...outgoingWebhook2Store.items[id], is_webhook_enabled: isEnabled },
      is_legacy: false,
    };

    outgoingWebhook2Store
      .update(id, data)
      .then(() => this.update())
      .then(() => openNotification(`Webhook has been ${isEnabled ? 'enabled' : 'disabled'}`))
      .catch(() => openErrorNotification('Webhook could not been updated'))
      .finally(() => this.setState({ confirmationModal: undefined }));
  };

  onLastRunClick = (id: OutgoingWebhook2['id']) => {
    const { history } = this.props;

    this.setState({ outgoingWebhook2Id: id, outgoingWebhook2Action: WebhookFormActionType.VIEW_LAST_RUN }, () =>
      history.push(`${PLUGIN_ROOT}/outgoing_webhooks_2/last_run/${id}`)
    );
  };

  handleOutgoingWebhookFormHide = () => {
    const { history } = this.props;

    this.setState({ outgoingWebhook2Id: undefined, outgoingWebhook2Action: undefined });

    history.push(`${PLUGIN_ROOT}/outgoing_webhooks_2`);
  };
}

function convertWebhookUrlToAction(urlAction: string) {
  if (urlAction === 'new') {
    return WebhookFormActionType.NEW;
  } else if (urlAction === 'copy') {
    return WebhookFormActionType.COPY;
  } else if (urlAction === 'edit') {
    return WebhookFormActionType.EDIT_SETTINGS;
  } else {
    return WebhookFormActionType.VIEW_LAST_RUN;
  }
}

export { OutgoingWebhooks2 };

export default withRouter(withMobXProviderContext(OutgoingWebhooks2));
