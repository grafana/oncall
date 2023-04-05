import React, { useRef } from 'react';

import { Badge, Button, HorizontalGroup, Icon, LoadingPlaceholder, Tooltip } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import Emoji from 'react-emoji-render';
import { RouteComponentProps, withRouter } from 'react-router-dom';

import CounterBadge from 'components/CounterBadge/CounterBadge';
import PageErrorHandlingWrapper, { PageBaseState } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper';
import { initErrorDataState } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper.helpers';
import { PageProps, WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';

import styles from './Integration2.module.scss';
import TeamName from 'containers/TeamName/TeamName';
import IntegrationLogo from 'components/IntegrationLogo/IntegrationLogo';
import Text from 'components/Text/Text';
import UserDisplayWithAvatar from 'containers/UserDisplay/UserDisplayWithAvatar';
import { WithContextMenu } from 'components/WithContextMenu/WithContextMenu';
import { AlertReceiveChannel } from 'models/alert_receive_channel';
import { openNotification } from 'utils';
import PluginLink from 'components/PluginLink/PluginLink';
import { PLUGIN_ROOT } from 'utils/consts';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { UserActions } from 'utils/authorization';
import IntegrationCollapsibleTreeView from 'components/IntegrationCollapsibleTreeView/IntegrationCollapsibleTreeView';
import Block from 'components/GBlock/Block';
import Tag from 'components/Tag/Tag';
import { getVar } from 'utils/DOM';

const cx = cn.bind(styles);

interface Integration2Props extends WithStoreProps, PageProps, RouteComponentProps<{ id: string }> {}

interface Integration2State extends PageBaseState {}

// This can be further improved by using a ref instead
const ACTIONS_LIST_WIDTH = 140;
const ACTIONS_LIST_BORDER = 2;

@observer
class Integration2 extends React.Component<Integration2Props, Integration2State> {
  constructor(props: Integration2Props) {
    super(props);

    this.state = {
      errorData: initErrorDataState(),
    };
  }

  async componentDidMount() {
    await this.loadIntegration();
  }

  render() {
    const { errorData } = this.state;
    const {
      store: { alertReceiveChannelStore, grafanaTeamStore },
      match: {
        params: { id },
      },
    } = this.props;

    const alertReceiveChannel = alertReceiveChannelStore.items[id];
    const channelFilterIds = alertReceiveChannelStore.channelFilterIds[id];
    const { isNotFoundError, isWrongTeamError } = errorData;

    if ((!alertReceiveChannel && !isNotFoundError && !isWrongTeamError) || !channelFilterIds) {
      return (
        <div className={cx('root')}>
          <LoadingPlaceholder text="Loading Integration..." />
        </div>
      );
    }

    const integration = alertReceiveChannelStore.getIntegration(alertReceiveChannel);
    const alertReceiveChannelCounter = alertReceiveChannelStore.counters[id];

    return (
      <PageErrorHandlingWrapper errorData={errorData} objectName="integration" pageName="Integration">
        {() => (
          <div className={cx('root')}>
            <div className={cx('integration__heading-container')}>
              <div className={cx('integration__heading')}>
                <h1 className={cx('integration__name')}>
                  <Emoji text={alertReceiveChannel.verbal_name} />
                </h1>
                <div className={cx('integration__actions')}>
                  <WithPermissionControlTooltip userAction={UserActions.IntegrationsTest}>
                    <Button
                      variant="secondary"
                      size="md"
                      onClick={() => this.onSendDemoAlertFn(id)}
                      data-testid="send-demo-alert"
                    >
                      Send demo alert
                    </Button>
                  </WithPermissionControlTooltip>

                  <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
                    <WithConfirm
                      title={`Are you sure to want to delete ${alertReceiveChannel.verbal_name} integration?`}
                      confirmText="Delete"
                    >
                      <Button
                        variant="destructive"
                        size="md"
                        onClick={() => this.onRemovalFn(id)}
                        data-testid="delete-integration"
                      >
                        Delete
                      </Button>
                    </WithConfirm>
                  </WithPermissionControlTooltip>

                  <WithContextMenu
                    renderMenuItems={() => (
                      <div className={cx('integration__actionsList')}>
                        <div className={cx('integration__actionItem')} onClick={() => this.onStartMaintenance(id)}>
                          <Text type="primary">Start Maintenance</Text>
                        </div>
                      </div>
                    )}
                  >
                    {({ openMenu }) => <HamburgerMenu openMenu={openMenu} />}
                  </WithContextMenu>
                </div>
              </div>
              {alertReceiveChannel.description && (
                <Text type="secondary" className={cx('integration__description')}>
                  {alertReceiveChannel.description}
                </Text>
              )}
              <HorizontalGroup>
                {alertReceiveChannelCounter && (
                  <Tooltip
                    placement="bottom-start"
                    content={
                      alertReceiveChannelCounter?.alerts_count +
                      ' alert' +
                      (alertReceiveChannelCounter?.alerts_count === 1 ? '' : 's') +
                      ' in ' +
                      alertReceiveChannelCounter?.alert_groups_count +
                      ' alert group' +
                      (alertReceiveChannelCounter?.alert_groups_count === 1 ? '' : 's')
                    }
                  >
                    {/* <span> is needed to be child, otherwise Tooltip won't render */}
                    <span>
                      <PluginLink
                        query={{ page: 'alert-groups', integration: alertReceiveChannel.id }}
                        className={cx('integration__counter')}
                      >
                        <Badge
                          text={
                            alertReceiveChannelCounter?.alerts_count +
                            '/' +
                            alertReceiveChannelCounter?.alert_groups_count
                          }
                          className={cx('integration__countersBadge')}
                          color={'blue'}
                        />
                      </PluginLink>
                    </span>
                  </Tooltip>
                )}

                <CounterBadge
                  borderType="success"
                  icon="link"
                  count={channelFilterIds.length}
                  tooltipTitle={`${channelFilterIds.length} Routes`}
                  tooltipContent={undefined}
                />
                <CounterBadge
                  borderType="warning"
                  icon="exclamation-triangle"
                  count={'1'}
                  tooltipTitle="1 Warning"
                  tooltipContent={undefined}
                />
                <HorizontalGroup spacing="xs">
                  <Text type="secondary">Type:</Text>
                  <HorizontalGroup spacing="none">
                    <IntegrationLogo scale={0.08} integration={integration} />
                    <Text type="secondary" size="small">
                      {integration?.display_name}
                    </Text>
                  </HorizontalGroup>
                </HorizontalGroup>
                <HorizontalGroup spacing="xs">
                  <Text type="secondary">Team:</Text>
                  <TeamName team={grafanaTeamStore.items[alertReceiveChannel.team]} size="small" />
                </HorizontalGroup>
                <HorizontalGroup spacing="xs">
                  <Text type="secondary">Created by:</Text>
                  <UserDisplayWithAvatar id={alertReceiveChannel.author as any}></UserDisplayWithAvatar>
                </HorizontalGroup>
              </HorizontalGroup>
            </div>

            <IntegrationCollapsibleTreeView>
              <IntegrationBlock
                heading={
                  <Tag color={getVar('--tag-secondary')}>
                    <Text type="primary" size="small">
                      HTTP Endpoint
                    </Text>
                  </Tag>
                }
                content={
                  <Text type="secondary">
                    <Text type="secondary">No alerts yet</Text>
                  </Text>
                }
              />
              <IntegrationBlock
                heading={
                  <Tag color={getVar('--tag-secondary')}>
                    <Text type="primary" size="small">
                      Templates
                    </Text>
                  </Tag>
                }
                content={<Text type="secondary">Templates</Text>}
              />
            </IntegrationCollapsibleTreeView>
          </div>
        )}
      </PageErrorHandlingWrapper>
    );
  }

  onRemovalFn = (id: AlertReceiveChannel['id']) => {
    const {
      store: { alertReceiveChannelStore },
      history,
    } = this.props;

    alertReceiveChannelStore.deleteAlertReceiveChannel(id).then(() => history.push(`${PLUGIN_ROOT}/integrations_2/`));
  };

  onStartMaintenance = (_id: AlertReceiveChannel['id']) => {};

  onSendDemoAlertFn = (id: AlertReceiveChannel['id']) => {
    const {
      store: { alertReceiveChannelStore },
    } = this.props;

    alertReceiveChannelStore.sendDemoAlert(id).then(() => {
      alertReceiveChannelStore.updateCounters();
      openNotification(<DemoNotification />);
    });
  };

  async loadIntegration() {
    const {
      store: { alertReceiveChannelStore },
      match: {
        params: { id },
      },
    } = this.props;

    const promises = [];

    if (!alertReceiveChannelStore.items[id]) {
      // See what happens if the request fails
      promises.push(alertReceiveChannelStore.loadItem(id));
    }

    if (!alertReceiveChannelStore.counters?.length) {
      promises.push(alertReceiveChannelStore.updateCounters());
    }

    if (!alertReceiveChannelStore.channelFilterIds[id]) {
      promises.push(await alertReceiveChannelStore.updateChannelFilters(id));
    }

    await Promise.all(promises);
  }
}

const DemoNotification: React.FC = () => {
  return (
    <div>
      Demo alert was generated. Find it on the
      <PluginLink query={{ page: 'alert-groups' }}> "Alert Groups" </PluginLink>
      page and make sure it didn't freak out your colleagues 😉
    </div>
  );
};

const HamburgerMenu: React.FC<{ openMenu: React.MouseEventHandler<HTMLElement> }> = ({ openMenu }) => {
  const ref = useRef<HTMLDivElement>();

  return (
    <div
      ref={ref}
      className={cx('hamburger-menu')}
      onClick={() => {
        const boundingRect = ref.current.getBoundingClientRect();

        openMenu({
          pageX: boundingRect.right - ACTIONS_LIST_WIDTH + ACTIONS_LIST_BORDER * 2,
          pageY: boundingRect.top + boundingRect.height,
        } as any);
      }}
    >
      <Icon size="sm" name="ellipsis-v" />
    </div>
  );
};

interface IntegrationBlockProps {
  heading: React.ReactNode;
  content: React.ReactNode;
}

const IntegrationBlock: React.FC<IntegrationBlockProps> = (props) => {
  const { heading, content } = props;
  return (
    <div className={cx('integrationBlock')}>
      <Block bordered shadowed className={cx('integrationBlock__heading')}>
        {heading}
      </Block>
      <div className={cx('integrationBlock__content')}>{content}</div>
    </div>
  );
};

export default withRouter(withMobXProviderContext(Integration2));
