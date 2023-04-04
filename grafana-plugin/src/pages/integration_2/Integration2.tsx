import React, { useRef } from 'react';

import { Button, HorizontalGroup, Icon, LoadingPlaceholder } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import Emoji from 'react-emoji-render';
import { RouteComponentProps, withRouter } from 'react-router-dom';

import InfoBadge from 'components/InfoBadge/InfoBadge';
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
                  <Button variant="secondary" size="sm" onClick={this.onSendDemoAlertFn} data-testid="send-demo-alert">
                    Send demo alert
                  </Button>

                  <WithContextMenu
                    renderMenuItems={() => (
                      <div className={cx('integration__actionsList')}>
                        <div className={cx('integration__actionItem')}>
                          <Text type="danger">Delete</Text>
                        </div>
                        <div className={cx('integration__actionItem')}>
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
                <InfoBadge borderType="primary" count={'0/0'} tooltipTitle="0/0 Alert Groups" tooltipContent={<></>} />
                <InfoBadge
                  borderType="success"
                  icon="link"
                  count={'1'}
                  tooltipTitle="1 Escalation Chain"
                  tooltipContent={<></>}
                />
                <InfoBadge
                  borderType="warning"
                  icon="exclamation-triangle"
                  count={'1'}
                  tooltipTitle="1 Warning"
                  tooltipContent={<></>}
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
            <div className={cx('integration__content')}></div>
          </div>
        )}
      </PageErrorHandlingWrapper>
    );
  }

  onSendDemoAlertFn: () => {};

  onMainActionsMenuOpen: () => {};

  async loadIntegration() {
    const {
      store: { alertReceiveChannelStore },
      match: {
        params: { id },
      },
    } = this.props;

    if (!alertReceiveChannelStore.items[id]) {
      // See what happens if the request fails
      await alertReceiveChannelStore.loadItem(id);
    }

    if (!alertReceiveChannelStore.channelFilterIds[id]) {
      await alertReceiveChannelStore.updateChannelFilters(id);
    }
  }
}

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

export default withRouter(withMobXProviderContext(Integration2));
