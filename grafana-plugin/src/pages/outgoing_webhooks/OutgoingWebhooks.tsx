import React from 'react';

import { css, cx } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { Button, ConfirmModal, ConfirmModalProps, HorizontalGroup, Icon, IconButton, withTheme2 } from '@grafana/ui';
import { observer } from 'mobx-react';
import { LegacyNavHeading } from 'navbar/LegacyNavHeading';
import CopyToClipboard from 'react-copy-to-clipboard';
import { RouteComponentProps, withRouter } from 'react-router-dom';
import { bem, getUtilStyles } from 'styles/utils.styles';

import { GTable } from 'components/GTable/GTable';
import { HamburgerContextMenu } from 'components/HamburgerContextMenu/HamburgerContextMenu';
import { LabelsTooltipBadge } from 'components/LabelsTooltipBadge/LabelsTooltipBadge';
import { PageErrorHandlingWrapper, PageBaseState } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper';
import {
  getWrongTeamResponseInfo,
  initErrorDataState,
} from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper.helpers';
import { PluginLink } from 'components/PluginLink/PluginLink';
import { Text } from 'components/Text/Text';
import { TextEllipsisTooltip } from 'components/TextEllipsisTooltip/TextEllipsisTooltip';
import { WebhookLastEventTimestamp } from 'components/Webhooks/WebhookLastEventTimestamp';
import { WebhookName } from 'components/Webhooks/WebhookName';
import { OutgoingWebhookForm } from 'containers/OutgoingWebhookForm/OutgoingWebhookForm';
import { RemoteFilters } from 'containers/RemoteFilters/RemoteFilters';
import { TeamName } from 'containers/TeamName/TeamName';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { FiltersValues } from 'models/filters/filters.types';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { AppFeature } from 'state/features';
import { PageProps, WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import { isUserActionAllowed, UserActions } from 'utils/authorization/authorization';
import { PAGE, PLUGIN_ROOT, TEXT_ELLIPSIS_CLASS } from 'utils/consts';
import { openErrorNotification, openNotification } from 'utils/utils';

import { WebhookFormActionType } from './OutgoingWebhooks.types';

interface OutgoingWebhooksProps extends WithStoreProps, PageProps, RouteComponentProps<{ id: string; action: string }> {
  theme: GrafanaTheme2;
}

interface OutgoingWebhooksState extends PageBaseState {
  outgoingWebhookAction?: WebhookFormActionType;
  outgoingWebhookId?: ApiSchemas['Webhook']['id'];
  confirmationModal: ConfirmModalProps;
}

@observer
class OutgoingWebhooks extends React.Component<OutgoingWebhooksProps, OutgoingWebhooksState> {
  state: OutgoingWebhooksState = {
    errorData: initErrorDataState(),
    confirmationModal: undefined,
  };

  componentDidMount() {
    this.props.store.outgoingWebhookStore.updateOutgoingWebhookPresetsOptions();
  }

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
      try {
        await store.outgoingWebhookStore.loadItem(id, true);
      } catch (error) {
        this.setState({ errorData: { ...getWrongTeamResponseInfo(error) }, outgoingWebhookAction: undefined });
      }
    }
  };

  update = () => {
    const {
      store: { outgoingWebhookStore },
    } = this.props;
    return outgoingWebhookStore.updateItems();
  };

  render() {
    const {
      store: { outgoingWebhookStore, filtersStore, grafanaTeamStore, hasFeature },
      history,
      match: {
        params: { id },
      },
    } = this.props;
    const { outgoingWebhookId, outgoingWebhookAction, errorData, confirmationModal } = this.state;

    const webhooks = outgoingWebhookStore.getSearchResult();

    const columns = [
      {
        width: '25%',
        title: 'Name',
        dataIndex: 'name',
        render: (name: string, webhook: ApiSchemas['Webhook']) => (
          <WebhookName
            name={name}
            isEnabled={webhook.is_webhook_enabled}
            displayAsLink
            onNameClick={() => this.onEditClick(webhook.id)}
          />
        ),
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
        title: 'Last event',
        render: (webhook: ApiSchemas['Webhook']) => (
          <WebhookLastEventTimestamp webhook={webhook} openDrawer={() => this.onLastRunClick(webhook.id)} />
        ),
      },
      ...(hasFeature(AppFeature.Labels)
        ? [
            {
              width: '10%',
              title: 'Labels',
              render: ({ labels }: ApiSchemas['Webhook']) => (
                <LabelsTooltipBadge
                  labels={labels}
                  onClick={(label) => filtersStore.applyLabelFilter(label, PAGE.Webhooks)}
                />
              ),
            },
          ]
        : []),
      {
        width: '15%',
        title: 'Team',
        render: (item: ApiSchemas['Webhook']) => this.renderTeam(item, grafanaTeamStore.items),
      },
      {
        width: '20%',
        key: 'action',
        render: this.renderActionButtons,
      },
    ];

    const styles = getStyles();

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
            <div className={styles.newWebhookButton}>
              <PluginLink
                query={{ page: 'outgoing_webhooks', id: 'new' }}
                disabled={!isUserActionAllowed(UserActions.OutgoingWebhooksWrite)}
              >
                <WithPermissionControlTooltip userAction={UserActions.OutgoingWebhooksWrite}>
                  <Button variant="primary" icon="plus">
                    New Outgoing Webhook
                  </Button>
                </WithPermissionControlTooltip>
              </PluginLink>
            </div>

            <div data-testid="outgoing-webhooks-table">
              {this.renderOutgoingWebhooksFilters()}
              <GTable
                emptyText={webhooks ? 'No outgoing webhooks found' : 'Loading...'}
                title={() => (
                  <div className={styles.header}>
                    <div className={styles.headerTitle}>
                      <LegacyNavHeading>
                        <Text.Title level={3}>Outgoing Webhooks</Text.Title>
                      </LegacyNavHeading>
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
                onDelete={async () => {
                  await this.onDeleteClick(outgoingWebhookId);
                  this.setState({ outgoingWebhookId: undefined, outgoingWebhookAction: undefined });
                  history.push(`${PLUGIN_ROOT}/outgoing_webhooks`);
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
      <div>
        <RemoteFilters
          query={query}
          page={PAGE.Webhooks}
          grafanaTeamStore={store.grafanaTeamStore}
          onChange={this.handleFiltersChange}
        />
      </div>
    );
  }

  handleFiltersChange = async (filters: FiltersValues, isOnMount: boolean) => {
    const { store } = this.props;

    const { outgoingWebhookStore } = store;

    await outgoingWebhookStore.updateItems(filters);
    if (isOnMount) {
      this.parseQueryParams();
    }
  };

  renderTeam(record: ApiSchemas['Webhook'], teams: any) {
    return <TeamName className={TEXT_ELLIPSIS_CLASS} team={teams[record.team]} />;
  }

  renderActionButtons = (record: ApiSchemas['Webhook']) => {
    return (
      <HamburgerContextMenu
        items={[
          {
            onClick: () => this.onLastRunClick(record.id),
            requiredPermission: UserActions.OutgoingWebhooksRead,
            label: <Text type="primary">View Last Event</Text>,
          },
          {
            onClick: () => this.onEditClick(record.id),
            requiredPermission: UserActions.OutgoingWebhooksWrite,
            label: <Text type="primary">Edit settings</Text>,
          },
          {
            onClick: () =>
              this.setState({
                confirmationModal: {
                  isOpen: true,
                  confirmText: 'Confirm',
                  dismissText: 'Cancel',
                  onConfirm: () => this.onDisableWebhook(record.id, !record.is_webhook_enabled),
                  title: `Are you sure you want to ${record.is_webhook_enabled ? 'disable' : 'enable'} webhook?`,
                } as ConfirmModalProps,
              }),
            requiredPermission: UserActions.OutgoingWebhooksWrite,
            label: <Text type="primary">{record.is_webhook_enabled ? 'Disable' : 'Enable'}</Text>,
          },
          {
            onClick: () => this.onCopyClick(record.id),
            requiredPermission: UserActions.OutgoingWebhooksWrite,
            label: <Text type="primary">Make a copy</Text>,
          },
          {
            label: (
              <CopyToClipboard key="uid" text={record.id} onCopy={() => openNotification('Webhook ID has been copied')}>
                <div>
                  <HorizontalGroup type="primary" spacing="xs">
                    <Icon name="clipboard-alt" />
                    <Text type="primary">UID: {record.id}</Text>
                  </HorizontalGroup>
                </div>
              </CopyToClipboard>
            ),
          },
          'divider',
          {
            onClick: () =>
              this.setState({
                confirmationModal: {
                  isOpen: true,
                  confirmText: 'Confirm',
                  dismissText: 'Cancel',
                  onConfirm: () => this.onDeleteClick(record.id),
                  body: 'The action cannot be undone.',
                  title: `Are you sure you want to delete webhook?`,
                } as Partial<ConfirmModalProps> as ConfirmModalProps,
              }),
            requiredPermission: UserActions.OutgoingWebhooksWrite,
            label: (
              <HorizontalGroup spacing="xs">
                <IconButton tooltip="Remove" tooltipPlacement="top" variant="destructive" name="trash-alt" />
                <Text type="danger">Delete Webhook</Text>
              </HorizontalGroup>
            ),
          },
        ]}
      />
    );
  };

  renderUrl = (url: string) => {
    const { theme } = this.props;
    const utilStyles = getUtilStyles(theme);

    return (
      <TextEllipsisTooltip content={url} placement="top">
        <Text className={cx(utilStyles.overflowChild, bem(utilStyles.overflowChild, 'line-3'))}>{url}</Text>
      </TextEllipsisTooltip>
    );
  };

  onDeleteClick = async (id: ApiSchemas['Webhook']['id']): Promise<void> => {
    const { store } = this.props;
    try {
      await store.outgoingWebhookStore.delete(id);
      await this.update();
      openNotification('Webhook has been removed');
    } catch (_err) {
      openNotification('Webook could not been removed');
    } finally {
      this.setState({ confirmationModal: undefined });
    }
  };

  onEditClick = (id: ApiSchemas['Webhook']['id']) => {
    const { history } = this.props;

    this.setState({ outgoingWebhookId: id, outgoingWebhookAction: WebhookFormActionType.EDIT_SETTINGS }, () =>
      history.push(`${PLUGIN_ROOT}/outgoing_webhooks/edit/${id}`)
    );
  };

  onCopyClick = (id: ApiSchemas['Webhook']['id']) => {
    const { history } = this.props;

    this.setState({ outgoingWebhookId: id, outgoingWebhookAction: WebhookFormActionType.COPY }, () =>
      history.push(`${PLUGIN_ROOT}/outgoing_webhooks/copy/${id}`)
    );
  };

  onDisableWebhook = async (id: ApiSchemas['Webhook']['id'], isEnabled: boolean) => {
    const {
      store: { outgoingWebhookStore },
    } = this.props;

    const data = {
      ...{ ...outgoingWebhookStore.items[id], is_webhook_enabled: isEnabled },
      is_legacy: false,
    };

    // don't pass trigger_type to backend as it's not editable
    delete data.trigger_type;

    try {
      await outgoingWebhookStore.update(id, data);
      await this.update();
      openNotification(`Webhook has been ${isEnabled ? 'enabled' : 'disabled'}`);
    } catch (_err) {
      openErrorNotification('Webhook could not been updated');
    }
    this.setState({ confirmationModal: undefined });
  };

  onLastRunClick = (id: ApiSchemas['Webhook']['id']) => {
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

const getStyles = () => {
  return {
    header: css`
      display: flex;
      align-items: center;
      width: 100%;
      padding-top: 12px;
    `,

    headerTitle: css`
      display: flex;
      align-items: baseline;
    `,

    newWebhookButton: css`
      position: absolute;
      right: 0;
      top: -48px;
    `,
  };
};

export const OutgoingWebhooksPage = withRouter(withMobXProviderContext(withTheme2(OutgoingWebhooks)));
