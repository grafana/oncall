import React, { useRef } from 'react';

import {
  Badge,
  Button,
  HorizontalGroup,
  VerticalGroup,
  Icon,
  LoadingPlaceholder,
  Tooltip,
  Input,
  InlineLabel,
  TextArea,
  Modal,
} from '@grafana/ui';
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
import MaskedInputField from '../../components/MaskedInputField/MaskedInputField';
import SourceCode from '../../components/SourceCode/SourceCode';
import CopyToClipboard from 'react-copy-to-clipboard';
import { useStore } from '../../state/useStore';

const cx = cn.bind(styles);

interface Integration2Props extends WithStoreProps, PageProps, RouteComponentProps<{ id: string }> {}

interface Integration2State extends PageBaseState {
  isDemoModalOpen: boolean;
}

// This can be further improved by using a ref instead
const ACTIONS_LIST_WIDTH = 160;
const ACTIONS_LIST_BORDER = 2;

@observer
class Integration2 extends React.Component<Integration2Props, Integration2State> {
  constructor(props: Integration2Props) {
    super(props);

    this.state = {
      errorData: initErrorDataState(),
      isDemoModalOpen: false,
    };
  }

  async componentDidMount() {
    await this.loadIntegration();
  }

  render() {
    const { errorData, isDemoModalOpen } = this.state;
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
                      onClick={() => this.setState({ isDemoModalOpen: true })}
                      data-testid="send-demo-alert"
                    >
                      Send demo alert
                    </Button>
                  </WithPermissionControlTooltip>

                  <WithContextMenu
                    renderMenuItems={({ closeMenu }) => (
                      <div className={cx('integration__actionsList')} id="integration-menu-options">
                        <div
                          className={cx('integration__actionItem')}
                          onClick={() => this.openIntegrationSettings(id, closeMenu)}
                        >
                          <Text type="primary">Integration Settings</Text>
                        </div>

                        <div className={cx('integration__actionItem')} onClick={() => this.openHearbeat(id, closeMenu)}>
                          Hearbeat
                        </div>

                        <div
                          className={cx('integration__actionItem')}
                          onClick={() => this.openStartMaintenance(id, closeMenu)}
                        >
                          <Text type="primary">Start Maintenance</Text>
                        </div>

                        <div className="thin-line-break" />

                        <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
                          <div className={cx('integration__actionItem')}>
                            <WithConfirm
                              title="Delete integration?"
                              body={
                                <>
                                  Are you sure you want to delete <Emoji text={alertReceiveChannel.verbal_name} />{' '}
                                  integration?
                                </>
                              }
                            >
                              <div onClick={() => this.deleteIntegration(id, closeMenu)}>
                                <div
                                  onClick={() => {
                                    // work-around to prevent 2 modals showing (withContextMenu and ConfirmModal)
                                    const contextMenuEl =
                                      document.querySelector<HTMLElement>('#integration-menu-options');
                                    if (contextMenuEl) {
                                      contextMenuEl.style.display = 'none';
                                    }
                                  }}
                                >
                                  <Text type="danger">Stop Maintenance</Text>
                                </div>
                              </div>
                            </WithConfirm>
                          </div>
                        </WithPermissionControlTooltip>
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
                  <HorizontalGroup justify={'space-between'}>
                    <HorizontalGroup>
                      <Tag color={getVar('--tag-secondary')}>
                        <Text type="primary" size="small">
                          HTTP Endpoint
                        </Text>
                      </Tag>
                      <MaskedInputField value={'test'} />
                    </HorizontalGroup>
                    <Button variant="secondary" size="sm" onClick={() => this.openHowToConnect()}>
                      How to connect
                    </Button>
                  </HorizontalGroup>
                }
                content={
                  <div className={cx('integration__alertsPanel')}>
                    <HorizontalGroup justify={'flex-start'} spacing={'xs'}>
                      <LoadingPlaceholder className={cx('loadingPlaceholder')} />
                      <Text type={'primary'}>No alerts yet; try to send a demo alert</Text>

                      <Icon name="list-ui-alt" size="md" />
                      <a href="/alerting/notifications" target="_blank">
                        <Text type={'link'}>Contact Point</Text>
                      </a>
                      <Text type={'secondary'}>and</Text>
                      <a href="/alerting/routes" target="_blank">
                        <Text type={'link'}>Notification Policy</Text>
                      </a>
                      <Text type={'secondary'}>created in Grafana Alerting</Text>
                    </HorizontalGroup>
                  </div>
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
                content={
                  <div className={cx('integration__templates')}>
                    <IntegrationBlockItem>
                      <Text type="secondary">
                        Templates are used to interpret alert from monitoring. Reduce noise, customize visualization
                      </Text>
                    </IntegrationBlockItem>

                    <IntegrationBlockItem>
                      <VerticalGroup>
                        <HorizontalGroup>
                          <InlineLabel width={20}>Grouping</InlineLabel>
                          <Input value="test" width={46} />
                          <Button variant="secondary" icon="edit" size="md" />
                          <Button variant="secondary" size="md">
                            <Text type="link">Help</Text>
                            <Icon name="angle-down" size="sm" />
                          </Button>
                        </HorizontalGroup>
                        <HorizontalGroup>
                          <InlineLabel width={20} tooltip={'TODO'}>
                            Auto resolve
                          </InlineLabel>
                          <Input value="test" width={46} />
                          <Button variant="secondary" icon={'edit'} size={'md'} />
                        </HorizontalGroup>
                      </VerticalGroup>
                    </IntegrationBlockItem>

                    <IntegrationBlockItem>
                      <VerticalGroup>
                        <Text type={'primary'}>Web</Text>
                        <HorizontalGroup>
                          <InlineLabel width={20}>Title</InlineLabel>
                          <Input value={'test'} width={46} />
                          <Button variant={'secondary'} icon={'edit'} size={'md'} />
                          <Button variant={'secondary'} icon={'times'} size={'md'} />
                        </HorizontalGroup>

                        <HorizontalGroup>
                          <InlineLabel width={20} tooltip={'TODO'}>
                            Message
                          </InlineLabel>
                          <TextArea value={'test'} width={46} />
                          <Button variant={'secondary'} icon={'edit'} size={'md'} />
                          <Button variant={'secondary'} icon={'times'} size={'md'} />
                        </HorizontalGroup>

                        <HorizontalGroup>
                          <InlineLabel width={20}>Image</InlineLabel>
                          <Input value={'text'} width={46} />
                          <Button variant={'secondary'} icon={'edit'} size={'md'} />
                          <Button variant={'secondary'} icon={'times'} size={'md'} />
                        </HorizontalGroup>
                      </VerticalGroup>
                    </IntegrationBlockItem>

                    <IntegrationBlockItem>
                      <VerticalGroup>
                        <HorizontalGroup>
                          <InlineLabel width={20}>Auto acknowledge</InlineLabel>
                          <Input value={'text'} width={46} />
                          <Button variant={'secondary'} icon={'edit'} size={'md'} />
                          <Button variant={'secondary'} icon={'times'} size={'md'} />
                          <Button variant="secondary" size="md">
                            <Text type="link">Help</Text>
                            <Icon name="angle-down" size="sm" />
                          </Button>
                        </HorizontalGroup>

                        <HorizontalGroup>
                          <InlineLabel width={20} tooltip={'TODO'}>
                            Source Link
                          </InlineLabel>
                          <Input value={'text'} width={46} />
                          <Button variant={'secondary'} icon={'edit'} size={'md'} />
                          <Button variant={'secondary'} icon={'times'} size={'md'} />
                        </HorizontalGroup>
                      </VerticalGroup>
                    </IntegrationBlockItem>

                    <IntegrationBlockItem>
                      <VerticalGroup>
                        <HorizontalGroup>
                          <InlineLabel width={20}>Phone Call</InlineLabel>
                          <Input value={'text'} width={46} />
                          <Button variant={'secondary'} icon={'edit'} size={'md'} />
                          <Button variant={'secondary'} icon={'times'} size={'md'} />
                          <Button variant="secondary" size="md">
                            <Text type="link">Help</Text>
                            <Icon name="angle-down" size="sm" />
                          </Button>
                        </HorizontalGroup>

                        <HorizontalGroup>
                          <InlineLabel width={20} tooltip={'TODO'}>
                            SMS
                          </InlineLabel>
                          <Input value={'text'} width={46} />
                          <Button variant={'secondary'} icon={'edit'} size={'md'} />
                          <Button variant={'secondary'} icon={'times'} size={'md'} />
                        </HorizontalGroup>
                      </VerticalGroup>
                    </IntegrationBlockItem>

                    <IntegrationBlockItem>
                      <VerticalGroup>
                        <Text type={'primary'}>Web</Text>
                        <HorizontalGroup>
                          <InlineLabel width={20} tooltip={'TODO'}>
                            Message
                          </InlineLabel>
                          <TextArea value={'text'} width={46} />
                          <Button variant={'secondary'} icon={'edit'} size={'md'} />
                          <Button variant={'secondary'} icon={'times'} size={'md'} />
                        </HorizontalGroup>
                      </VerticalGroup>
                    </IntegrationBlockItem>

                    <IntegrationBlockItem>
                      <VerticalGroup>
                        <Text type={'secondary'}>By default alert groups rendered based on Web templates.</Text>
                        <Text type={'secondary'}>
                          Customise how they rendered in SMS, Phone Calls, Mobile App, Slack, Telegram, MS Teams{' '}
                        </Text>
                        <Button variant={'secondary'} size={'md'}>
                          <Icon name={'plus'} size={'md'} />
                          Customise templates
                        </Button>
                      </VerticalGroup>
                    </IntegrationBlockItem>
                  </div>
                }
              />
            </IntegrationCollapsibleTreeView>

            <IntegrationSendDemoPayloadModal
              alertReceiveChannel={alertReceiveChannel}
              isOpen={isDemoModalOpen}
              onCancel={() => this.setState({ isDemoModalOpen: false })}
            />
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

  openHowToConnect = () => {};

  deleteIntegration = (_id: AlertReceiveChannel['id'], _closeMenu: () => void) => {};

  openIntegrationSettings = (_id: AlertReceiveChannel['id'], _closeMenu: () => void) => {};

  openStartMaintenance = (_id: AlertReceiveChannel['id'], _closeMenu: () => void) => {};

  openHearbeat = (_id: AlertReceiveChannel['id'], _closeMenu: () => void) => {};

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

interface IntegrationBlockItemProps {
  children: React.ReactNode;
}

const IntegrationBlockItem: React.FC<IntegrationBlockItemProps> = (props) => {
  return (
    <div className={cx('blockItem')}>
      <div className={cx('blockItem__leftDelimitator')} />
      <div className={cx('blockItem__content')}>{props.children}</div>
    </div>
  );
};

interface IntegrationSendDemoPayloadModalProps {
  isOpen: boolean;
  alertReceiveChannel: AlertReceiveChannel;
  onCancel: () => void;
}

const IntegrationSendDemoPayloadModal: React.FC<IntegrationSendDemoPayloadModalProps> = ({
  alertReceiveChannel,
  isOpen,
  onCancel,
}) => {
  const { alertReceiveChannelStore } = useStore();

  console.log('here we are');

  return (
    <Modal
      closeOnEscape
      isOpen={isOpen}
      onDismiss={onCancel}
      title={`Send demo alert to ${alertReceiveChannel.verbal_name}`}
    >
      <VerticalGroup>
        <HorizontalGroup spacing={'xs'}>
          <Text type={'secondary'}>Alert Payload</Text>
          <Tooltip content={'TODO'} placement={'top-start'}>
            <Icon name={'info-circle'} />
          </Tooltip>
        </HorizontalGroup>

        <SourceCode showCopyToClipboard={false}>{getDemoAlertJSON()}</SourceCode>

        <HorizontalGroup justify={'flex-end'} spacing={'xs'}>
          <Button variant={'secondary'} onClick={onCancel}>
            Cancel
          </Button>
          <CopyToClipboard text={getCurlText()} onCopy={() => openNotification('CURL copied!')}>
            <Button variant={'secondary'}>Copy as CURL</Button>
          </CopyToClipboard>
          <Button variant={'primary'} onClick={sendDemoAlert}>
            Send Alert
          </Button>
        </HorizontalGroup>
      </VerticalGroup>
    </Modal>
  );

  function sendDemoAlert() {
    alertReceiveChannelStore.sendDemoAlert(alertReceiveChannel.id).then(() => {
      alertReceiveChannelStore.updateCounters();
      openNotification(<DemoNotification />);
    });
  }

  function getCurlText() {
    // TODO add this
    return '';
  }

  function getDemoAlertJSON() {
    return JSON.stringify(
      {
        alert_uid: '08d6891a-835c-e661-39fa-96b6a9e26552',
        title: 'The whole system is down',
        image_url: 'https://http.cat/500',
        state: 'alerting',
        link_to_upstream_details: 'https://en.wikipedia.org/wiki/Downtime',
        message: 'Smth happened. Oh no!',
      },
      null,
      4
    );
  }
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
