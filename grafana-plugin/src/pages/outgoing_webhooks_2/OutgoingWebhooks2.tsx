import React from 'react';

import { Button, HorizontalGroup, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import LegacyNavHeading from 'navbar/LegacyNavHeading';
import { RouteComponentProps, withRouter } from 'react-router-dom';

import GTable from 'components/GTable/GTable';
import PageErrorHandlingWrapper, { PageBaseState } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper';
import {
  getWrongTeamResponseInfo,
  initErrorDataState,
} from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper.helpers';
import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import OutgoingWebhook2Form from 'containers/OutgoingWebhook2Form/OutgoingWebhook2Form';
import OutgoingWebhook2Status from 'containers/OutgoingWebhook2Status/OutgoingWebhook2Status';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { ActionDTO } from 'models/action';
import { OutgoingWebhook2 } from 'models/outgoing_webhook_2/outgoing_webhook_2.types';
import { PageProps, WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import { isUserActionAllowed, UserActions } from 'utils/authorization';
import { PLUGIN_ROOT } from 'utils/consts';

import styles from './OutgoingWebhooks2.module.css';
import moment from 'moment-timezone';
import { MatchMediaTooltip } from 'components/MatchMediaTooltip/MatchMediaTooltip';

const cx = cn.bind(styles);

interface OutgoingWebhooks2Props extends WithStoreProps, PageProps, RouteComponentProps<{ id: string }> {}

interface OutgoingWebhooks2State extends PageBaseState {
  outgoingWebhook2IdToEdit?: OutgoingWebhook2['id'] | 'new';
  outgoingWebhook2IdToShowStatus?: OutgoingWebhook2['id'];
}

@observer
class OutgoingWebhooks2 extends React.Component<OutgoingWebhooks2Props, OutgoingWebhooks2State> {
  state: OutgoingWebhooks2State = {
    errorData: initErrorDataState(),
  };

  async componentDidMount() {
    this.update().then(this.parseQueryParams);
  }

  componentDidUpdate(prevProps: OutgoingWebhooks2Props) {
    if (prevProps.match.params.id !== this.props.match.params.id) {
      this.parseQueryParams();
    }
  }

  parseQueryParams = async () => {
    this.setState((_prevState) => ({
      errorData: initErrorDataState(),
      outgoingWebhook2IdToEdit: undefined,
    })); // reset state on query parse

    const {
      store,
      match: {
        params: { id },
      },
    } = this.props;

    if (!id) {
      return;
    }

    let outgoingWebhook2: OutgoingWebhook2 | void = undefined;
    const isNewWebhook = id === 'new';

    if (!isNewWebhook) {
      outgoingWebhook2 = await store.outgoingWebhook2Store
        .loadItem(id, true)
        .catch((error) => this.setState({ errorData: { ...getWrongTeamResponseInfo(error) } }));
    }

    if (outgoingWebhook2 || isNewWebhook) {
      this.setState({ outgoingWebhook2IdToEdit: id });
    }
  };

  update = () => {
    const { store } = this.props;

    return store.outgoingWebhook2Store.updateItems();
  };

  render() {
    const { store, query } = this.props;
    const { outgoingWebhook2IdToEdit, outgoingWebhook2IdToShowStatus, errorData } = this.state;

    const webhooks = store.outgoingWebhook2Store.getSearchResult();

    const columns = [
      {
        width: '25%',
        title: 'Name',
        dataIndex: 'name',
      },
      {
        width: '5%',
        title: 'Trigger type',
        dataIndex: 'trigger_type_name',
      },
      {
        width: '5%',
        title: 'HTTP method',
        dataIndex: 'http_method',
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
        dataIndex: 'last_run',
        render: this.renderLastRun,
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
        objectName="outgoing webhook 2"
        pageName="outgoing_webhooks_2"
        itemNotFoundMessage={`Outgoing webhook with id=${query?.id} is not found. Please select outgoing webhook from the list.`}
      >
        {() => (
          <>
            <div className={cx('root')}>
              <GTable
                emptyText={webhooks ? 'No outgoing webhooks found' : 'Loading...'}
                title={() => (
                  <div className={cx('header')}>
                    <LegacyNavHeading>
                      <VerticalGroup>
                        <Text.Title level={3}>Outgoing Webhooks 2</Text.Title>
                        <Text type="secondary">
                          ⚠️ Preview Functionality! Things will change and things will break! Do not use for critical
                          production processes!
                        </Text>
                      </VerticalGroup>
                    </LegacyNavHeading>
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
            {outgoingWebhook2IdToEdit && !outgoingWebhook2IdToShowStatus && (
              <OutgoingWebhook2Form
                id={outgoingWebhook2IdToEdit}
                onUpdate={this.update}
                onHide={this.handleOutgoingWebhookFormHide}
              />
            )}
            {outgoingWebhook2IdToShowStatus && (
              <OutgoingWebhook2Status
                id={outgoingWebhook2IdToShowStatus}
                onUpdate={this.update}
                onHide={this.handleOutgoingWebhookFormHide}
              />
            )}
          </>
        )}
      </PageErrorHandlingWrapper>
    );
  }

  renderActionButtons = (record: ActionDTO) => {
    return (
      <HorizontalGroup justify="flex-end">
        <WithPermissionControlTooltip key={'status_action'} userAction={UserActions.OutgoingWebhooksRead}>
          <Button onClick={this.getStatusClickHandler(record.id)} fill="text">
            Status
          </Button>
        </WithPermissionControlTooltip>
        <WithPermissionControlTooltip key={'edit_action'} userAction={UserActions.OutgoingWebhooksWrite}>
          <Button onClick={this.getEditClickHandler(record.id)} fill="text">
            Edit
          </Button>
        </WithPermissionControlTooltip>
        <WithPermissionControlTooltip key={'delete_action'} userAction={UserActions.OutgoingWebhooksWrite}>
          <WithConfirm>
            <Button onClick={this.getDeleteClickHandler(record.id)} fill="text" variant="destructive">
              Delete
            </Button>
          </WithConfirm>
        </WithPermissionControlTooltip>
      </HorizontalGroup>
    );
  };

  renderUrl(url: string) {
    console.log('url');
    return (
      <div className="table__email-content">
        <Text type="secondary">
          <MatchMediaTooltip placement="top" content={url} maxWidth={300}>
            <span>{url}</span>
          </MatchMediaTooltip>
        </Text>
      </div>
    );
  }

  renderLastRun(_lastRun: string, webhook: OutgoingWebhook2) {
    const lastRunMoment = moment(webhook.last_status_log?.last_run_at);

    return (
      <VerticalGroup spacing="none">
        <Text type="secondary">{lastRunMoment.format('MMM DD, YYYY')}</Text>
        <Text type="secondary">{lastRunMoment.format('hh:mm A')}</Text>
      </VerticalGroup>
    );
  }

  getDeleteClickHandler = (id: OutgoingWebhook2['id']) => {
    const { store } = this.props;

    return () => {
      store.outgoingWebhook2Store.delete(id).then(this.update);
    };
  };

  getEditClickHandler = (id: OutgoingWebhook2['id']) => {
    const { history } = this.props;

    return () => {
      this.setState({ outgoingWebhook2IdToEdit: id, outgoingWebhook2IdToShowStatus: undefined });

      history.push(`${PLUGIN_ROOT}/outgoing_webhooks_2/${id}`);
    };
  };

  handleOutgoingWebhookFormHide = () => {
    const { history } = this.props;
    this.setState({ outgoingWebhook2IdToEdit: undefined, outgoingWebhook2IdToShowStatus: undefined });

    history.push(`${PLUGIN_ROOT}/outgoing_webhooks_2`);
  };

  getStatusClickHandler = (id: OutgoingWebhook2['id']) => {
    return () => {
      const { history } = this.props;
      this.setState({ outgoingWebhook2IdToEdit: undefined, outgoingWebhook2IdToShowStatus: id });

      history.push(`${PLUGIN_ROOT}/outgoing_webhooks_2/${id}`);
    };
  };
}

export { OutgoingWebhooks2 };

export default withRouter(withMobXProviderContext(OutgoingWebhooks2));
