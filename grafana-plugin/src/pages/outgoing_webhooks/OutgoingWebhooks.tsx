import React from 'react';

import {
  Button,
  ConfirmModal,
  ConfirmModalProps,
  HorizontalGroup,
  Icon,
  IconButton,
  VerticalGroup,
  WithContextMenu,
} from '@grafana/ui';
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
import OutgoingWebhookForm from 'containers/OutgoingWebhookForm/OutgoingWebhookForm';
import RemoteFilters from 'containers/RemoteFilters/RemoteFilters';
import TeamName from 'containers/TeamName/TeamName';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { FiltersValues } from 'models/filters/filters.types';
import { OutgoingWebhook } from 'models/outgoing_webhook/outgoing_webhook.types';
import { PageProps, WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import { openErrorNotification, openNotification } from 'utils';
import { isUserActionAllowed, UserActions } from 'utils/authorization';
import { PLUGIN_ROOT } from 'utils/consts';

import styles from './OutgoingWebhooks.module.scss';
import { WebhookFormActionType } from './OutgoingWebhooks.types';

const cx = cn.bind(styles);

interface OutgoingWebhooksProps
  extends WithStoreProps,
    PageProps,
    RouteComponentProps<{ id: string; action: string }> {}

interface OutgoingWebhooksState extends PageBaseState {
  outgoingWebhookAction?: WebhookFormActionType;
  outgoingWebhookId?: OutgoingWebhook['id'];
  confirmationModal: ConfirmModalProps;
}

@observer
class OutgoingWebhooks extends React.Component<OutgoingWebhooksProps, OutgoingWebhooksState> {
  state: OutgoingWebhooksState = {
    errorData: initErrorDataState(),
    confirmationModal: undefined,
  };

  componentDidUpdate(prevProps: OutgoingWebhooksProps) {
    if (prevProps.match.params.id !== this.props.match.params.id && !this.state.outgoingWebhookAction) {
      this.parseQueryParams();
    }
  }

  parseQueryParams = async () => {
    this.setState((_prevState) => ({
      errorData: initErrorDataState(),
      outgoingWebhookId: undefined,
    })); // reset state on query parse

    const {
      store,
      match: {
        params: { id, action },
      },
    } = this.props;

    if (action) {
      this.setState({ outgoingWebhookId: id, outgoingWebhookAction: convertWebhookUrlToAction(action) });
    }

    const isNewWebhook = id === 'new';
    if (isNewWebhook) {
      this.setState({ outgoingWebhookId: id, outgoingWebhookAction: WebhookFormActionType.NEW });
    } else if (id) {
      await store.outgoingWebhookStore
        .loadItem(id, true)
        .catch((error) =>
          this.setState({ errorData: { ...getWrongTeamResponseInfo(error) }, outgoingWebhookAction: undefined })
        );
    }
  };

  update = () => {
    const { store } = this.props;
    return store.outgoingWebhookStore.updateItems();
  };

  render() {
    const {
      store,
      history,
      match: {
        params: { id },
      },
    } = this.props;
    const { outgoingWebhookId, outgoingWebhookAction, errorData, confirmationModal } = this.state;

    const webhooks = store.outgoingWebhookStore.getSearchResult();

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

    return (
      <PageErrorHandlingWrapper
        errorData={errorData}
        objectName="outgoing webhook"
        pageName="outgoing_webhooks"
        itemNotFoundMessage={`Outgoing webhook with id=${id} was not found. Please select outgoing webhook from the list.`}
      >
        {() => (
          <>
            {confirmationModal && (
              <ConfirmModal
                {...(confirmationModal as ConfirmModalProps)}
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
                      <LegacyNavHeading>
                        <Text.Title level={3}>Outgoing Webhooks</Text.Title>
                      </LegacyNavHeading>
                    </div>
                    <div className="u-pull-right">
                      <PluginLink
                        query={{ page: 'outgoing_webhooks', id: 'new' }}
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

            {outgoingWebhookId && outgoingWebhookAction && (
              <OutgoingWebhookForm
                id={outgoingWebhookId}
                action={outgoingWebhookAction}
                onUpdate={this.update}
                onHide={this.handleOutgoingWebhookFormHide}
                onDelete={() => {
                  this.onDeleteClick(outgoingWebhookId).then(() => {
                    this.setState({ outgoingWebhookId: undefined, outgoingWebhookAction: undefined });
                    history.push(`${PLUGIN_ROOT}/outgoing_webhooks`);
                  });
                }}
              />
            )}
          </>
        )}
      </PageErrorHandlingWrapper>
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

    const { outgoingWebhookStore } = store;

    outgoingWebhookStore.updateItems(filters).then(() => {
      if (isOnMount) {
        this.parseQueryParams();
      }
    });
  };

  renderTeam(record: OutgoingWebhook, teams: any) {
    return <TeamName team={teams[record.team]} />;
  }

  renderActionButtons = (record: OutgoingWebhook) => {
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
                    title: `Are you sure you want to ${record.is_webhook_enabled ? 'disable' : 'enable'} webhook?`,
                  } as ConfirmModalProps,
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

            <CopyToClipboard text={record.id} onCopy={() => openNotification('Webhook ID has been copied')}>
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
                    body: 'The action cannot be undone.',
                    title: `Are you sure you want to delete webhook?`,
                  } as Partial<ConfirmModalProps> as ConfirmModalProps,
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

  renderLastRun(record: OutgoingWebhook) {
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

  onDeleteClick = (id: OutgoingWebhook['id']): Promise<void> => {
    const { store } = this.props;
    return store.outgoingWebhookStore
      .delete(id)
      .then(this.update)
      .then(() => openNotification('Webhook has been removed'))
      .catch(() => openNotification('Webook could not been removed'))
      .finally(() => this.setState({ confirmationModal: undefined }));
  };

  onEditClick = (id: OutgoingWebhook['id']) => {
    const { history } = this.props;

    this.setState({ outgoingWebhookId: id, outgoingWebhookAction: WebhookFormActionType.EDIT_SETTINGS }, () =>
      history.push(`${PLUGIN_ROOT}/outgoing_webhooks/edit/${id}`)
    );
  };

  onCopyClick = (id: OutgoingWebhook['id']) => {
    const { history } = this.props;

    this.setState({ outgoingWebhookId: id, outgoingWebhookAction: WebhookFormActionType.COPY }, () =>
      history.push(`${PLUGIN_ROOT}/outgoing_webhooks/copy/${id}`)
    );
  };

  onDisableWebhook = (id: OutgoingWebhook['id'], isEnabled: boolean) => {
    const {
      store: { outgoingWebhookStore },
    } = this.props;

    const data = {
      ...{ ...outgoingWebhookStore.items[id], is_webhook_enabled: isEnabled },
      is_legacy: false,
    };

    outgoingWebhookStore
      .update(id, data)
      .then(() => this.update())
      .then(() => openNotification(`Webhook has been ${isEnabled ? 'enabled' : 'disabled'}`))
      .catch(() => openErrorNotification('Webhook could not been updated'))
      .finally(() => this.setState({ confirmationModal: undefined }));
  };

  onLastRunClick = (id: OutgoingWebhook['id']) => {
    const { history } = this.props;

    this.setState({ outgoingWebhookId: id, outgoingWebhookAction: WebhookFormActionType.VIEW_LAST_RUN }, () =>
      history.push(`${PLUGIN_ROOT}/outgoing_webhooks/last_run/${id}`)
    );
  };

  handleOutgoingWebhookFormHide = () => {
    const { history } = this.props;

    this.setState({ outgoingWebhookId: undefined, outgoingWebhookAction: undefined });

    history.push(`${PLUGIN_ROOT}/outgoing_webhooks`);
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

export { OutgoingWebhooks };

export default withRouter(withMobXProviderContext(OutgoingWebhooks));
