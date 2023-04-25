import React, { useRef } from 'react';

import {
  Badge,
  Button,
  HorizontalGroup,
  VerticalGroup,
  Icon,
  LoadingPlaceholder,
  Tooltip,
  Modal,
  ButtonCascader,
  CascaderOption,
} from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import CopyToClipboard from 'react-copy-to-clipboard';
import Emoji from 'react-emoji-render';
import { RouteComponentProps, withRouter } from 'react-router-dom';

import { TemplateForEdit } from 'components/AlertTemplates/AlertTemplatesForm.config';
import CounterBadge from 'components/CounterBadge/CounterBadge';
import IntegrationCollapsibleTreeView from 'components/IntegrationCollapsibleTreeView/IntegrationCollapsibleTreeView';
import IntegrationLogo from 'components/IntegrationLogo/IntegrationLogo';
import MaskedInputField from 'components/MaskedInputField/MaskedInputField';
import MonacoJinja2Editor from 'components/MonacoJinja2Editor/MonacoJinja2Editor';
import PageErrorHandlingWrapper, { PageBaseState } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper';
import { initErrorDataState } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper.helpers';
import PluginLink from 'components/PluginLink/PluginLink';
import SourceCode from 'components/SourceCode/SourceCode';
import Tag from 'components/Tag/Tag';
import Text from 'components/Text/Text';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import { WithContextMenu } from 'components/WithContextMenu/WithContextMenu';
import IntegrationTemplate from 'containers/IntegrationTemplate/IntegrationTemplate';
import TeamName from 'containers/TeamName/TeamName';
import UserDisplayWithAvatar from 'containers/UserDisplay/UserDisplayWithAvatar';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { AlertReceiveChannel } from 'models/alert_receive_channel';
import { PageProps, WithStoreProps } from 'state/types';
import { useStore } from 'state/useStore';
import { withMobXProviderContext } from 'state/withStore';
import { openNotification, openErrorNotification } from 'utils';
import { getVar } from 'utils/DOM';
import { UserActions } from 'utils/authorization';
import { PLUGIN_ROOT } from 'utils/consts';

import styles from './Integration2.module.scss';
import IntegrationBlockItem from './IntegrationBlockItem';
import {
  INTEGRATION_DEMO_PAYLOAD,
  INTEGRATION_TEMPLATES_LIST,
  MONACO_INPUT_HEIGHT_SMALL,
  MONACO_INPUT_HEIGHT_TALL,
} from './Integration2.config';
import IntegrationRouteDisplay from './IntegrationRouteDisplay';
import IntegrationBlock from './IntegrationBlock';
import IntegrationTemplateBlock from './IntegrationTemplateBlock';

const cx = cn.bind(styles);

interface Integration2Props extends WithStoreProps, PageProps, RouteComponentProps<{ id: string }> {}

interface Integration2State extends PageBaseState {
  isDemoModalOpen: boolean;
  isEditTemplateModalOpen: boolean;
  selectedTemplate: TemplateForEdit;
}

const ACTIONS_LIST_WIDTH = 160;
const ACTIONS_LIST_BORDER = 2;

const MONACO_OPTIONS = {
  renderLineHighlight: false,
  readOnly: true,
  scrollbars: {
    vertical: 'hidden',
    horizontal: 'hidden',
    verticalScrollbarSize: 0,
    handleMouseWheel: false,
  },
  hideCursorInOverviewRuler: true,
  minimap: { enabled: false },
  cursorStyle: {
    display: 'none',
  },
};

@observer
class Integration2 extends React.Component<Integration2Props, Integration2State> {
  constructor(props: Integration2Props) {
    super(props);

    this.state = {
      errorData: initErrorDataState(),
      isDemoModalOpen: false,
      isEditTemplateModalOpen: false,
      selectedTemplate: undefined,
    };
  }

  async componentDidMount() {
    const {
      match: {
        params: { id },
      },
    } = this.props;
    const {
      store: { alertReceiveChannelStore },
    } = this.props;

    await Promise.all([this.loadIntegration(), alertReceiveChannelStore.updateTemplates(id)]);
  }

  render() {
    const { errorData, isDemoModalOpen, isEditTemplateModalOpen, selectedTemplate } = this.state;
    const {
      store: { alertReceiveChannelStore, grafanaTeamStore },
      match: {
        params: { id },
      },
    } = this.props;

    const { isNotFoundError, isWrongTeamError } = errorData;

    const alertReceiveChannel = alertReceiveChannelStore.items[id];
    const channelFilterIds = alertReceiveChannelStore.channelFilterIds[id];
    const templates = alertReceiveChannelStore.templates[id];

    if ((!alertReceiveChannel && !isNotFoundError && !isWrongTeamError) || !channelFilterIds || !templates) {
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
                      <LoadingPlaceholder text="Loading..." className={cx('loadingPlaceholder')} />
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
                        <IntegrationTemplateBlock
                          label={'Grouping'}
                          renderInput={() => (
                            <div className={cx('input', 'input--short')}>
                              <MonacoJinja2Editor
                                value={templates['grouping_id_template'] || ''}
                                disabled={true}
                                height={MONACO_INPUT_HEIGHT_SMALL}
                                data={templates}
                                showLineNumbers={false}
                                monacoOptions={MONACO_OPTIONS}
                              />
                            </div>
                          )}
                          showHelp
                          onEdit={() =>
                            this.openEditTemplateModal(
                              'Grouping',
                              templates['grouping_id_template'],
                              'grouping_id_template'
                            )
                          }
                        />

                        <IntegrationTemplateBlock
                          label={'Auto resolve'}
                          renderInput={() => (
                            <div className={cx('input', 'input--short')}>
                              <MonacoJinja2Editor
                                value={templates['resolve_condition_template'] || ''}
                                disabled={true}
                                height={MONACO_INPUT_HEIGHT_SMALL}
                                data={templates}
                                showLineNumbers={false}
                                monacoOptions={MONACO_OPTIONS}
                              />
                            </div>
                          )}
                          onEdit={() =>
                            this.openEditTemplateModal(
                              'Autoresolve',
                              templates['resolve_condition_template'],
                              'resolve_condition_template'
                            )
                          }
                        />
                      </VerticalGroup>
                    </IntegrationBlockItem>

                    <IntegrationBlockItem>
                      <VerticalGroup>
                        <Text type={'primary'}>Web</Text>

                        <IntegrationTemplateBlock
                          label={'Title'}
                          renderInput={() => (
                            <div className={cx('input', 'input--long')}>
                              <MonacoJinja2Editor
                                value={templates['web_title_template'] || ''}
                                disabled={true}
                                height={MONACO_INPUT_HEIGHT_TALL}
                                data={templates}
                                showLineNumbers={false}
                                monacoOptions={MONACO_OPTIONS}
                              />
                            </div>
                          )}
                          onEdit={() =>
                            this.openEditTemplateModal(
                              'Web title',
                              templates['web_title_template'],
                              'web_title_template'
                            )
                          }
                        />

                        <IntegrationTemplateBlock
                          label={'Message'}
                          renderInput={() => (
                            <div className={cx('input', 'input--long')}>
                              <MonacoJinja2Editor
                                value={templates['web_message_template'] || ''}
                                disabled={true}
                                height={MONACO_INPUT_HEIGHT_TALL}
                                data={templates}
                                showLineNumbers={false}
                                monacoOptions={MONACO_OPTIONS}
                              />
                            </div>
                          )}
                          onEdit={() =>
                            this.openEditTemplateModal(
                              'Web message',
                              templates['web_message_template'],
                              'web_message_template'
                            )
                          }
                        />

                        <IntegrationTemplateBlock
                          label={'Image'}
                          renderInput={() => (
                            <div className={cx('input', 'input--long')}>
                              <MonacoJinja2Editor
                                value={templates['web_image_url_template'] || ''}
                                disabled={true}
                                height={MONACO_INPUT_HEIGHT_SMALL}
                                data={templates}
                                showLineNumbers={false}
                                monacoOptions={MONACO_OPTIONS}
                              />
                            </div>
                          )}
                          onEdit={() =>
                            this.openEditTemplateModal(
                              'Web image',
                              templates['web_image_url_template'],
                              'web_image_url_template'
                            )
                          }
                        />
                      </VerticalGroup>
                    </IntegrationBlockItem>

                    <IntegrationBlockItem>
                      <VerticalGroup>
                        <IntegrationTemplateBlock
                          label={'Auto acknowledge'}
                          renderInput={() => (
                            <div className={cx('input', 'input--short')}>
                              <MonacoJinja2Editor
                                value={templates['acknowledge_condition_template'] || ''}
                                disabled={true}
                                height={MONACO_INPUT_HEIGHT_SMALL}
                                data={templates}
                                showLineNumbers={false}
                                monacoOptions={MONACO_OPTIONS}
                              />
                            </div>
                          )}
                          onEdit={() =>
                            this.openEditTemplateModal(
                              'Auto acknowledge',
                              templates['acknowledge_condition_template'],
                              'acknowledge_condition_template'
                            )
                          }
                          showHelp
                        />

                        <IntegrationTemplateBlock
                          label={'Source Link'}
                          renderInput={() => (
                            <div className={cx('input', 'input--short')}>
                              <MonacoJinja2Editor
                                value={templates['source_link_template'] || ''}
                                disabled={true}
                                height={MONACO_INPUT_HEIGHT_SMALL}
                                data={templates}
                                showLineNumbers={false}
                                monacoOptions={MONACO_OPTIONS}
                              />
                            </div>
                          )}
                          onEdit={() =>
                            this.openEditTemplateModal(
                              'Source link',
                              templates['source_link_template'],
                              'source_link_template'
                            )
                          }
                        />
                      </VerticalGroup>
                    </IntegrationBlockItem>

                    <IntegrationBlockItem>
                      <VerticalGroup>
                        <IntegrationTemplateBlock
                          label={'Phone Call'}
                          renderInput={() => (
                            <div className={cx('input', 'input--short')}>
                              <MonacoJinja2Editor
                                value={templates['phone_call_title_template'] || ''}
                                disabled={true}
                                height={MONACO_INPUT_HEIGHT_SMALL}
                                data={templates}
                                showLineNumbers={false}
                                monacoOptions={MONACO_OPTIONS}
                              />
                            </div>
                          )}
                          onEdit={() =>
                            this.openEditTemplateModal(
                              'Phone call',
                              templates['phone_call_title_template'],
                              'phone_call_title_template'
                            )
                          }
                          showHelp
                        />

                        <IntegrationTemplateBlock
                          label={'SMS'}
                          renderInput={() => (
                            <div className={cx('input', 'input--short')}>
                              <MonacoJinja2Editor
                                value={templates['sms_title_template'] || ''}
                                disabled={true}
                                height={MONACO_INPUT_HEIGHT_SMALL}
                                data={templates}
                                showLineNumbers={false}
                                monacoOptions={MONACO_OPTIONS}
                              />
                            </div>
                          )}
                          onEdit={() =>
                            this.openEditTemplateModal('SMS', templates['sms_title_template'], 'sms_title_template')
                          }
                        />
                      </VerticalGroup>
                    </IntegrationBlockItem>

                    <IntegrationBlockItem>
                      <VerticalGroup>
                        <Text type={'primary'}>Slack</Text>

                        <IntegrationTemplateBlock
                          label={'Title'}
                          renderInput={() => (
                            <div className={cx('input', 'input--long')}>
                              <MonacoJinja2Editor
                                value={templates['slack_title_template'] || ''}
                                disabled={true}
                                height={MONACO_INPUT_HEIGHT_SMALL}
                                data={templates}
                                showLineNumbers={false}
                                monacoOptions={MONACO_OPTIONS}
                              />
                            </div>
                          )}
                          onEdit={() =>
                            this.openEditTemplateModal(
                              'Slack title',
                              templates['slack_title_template'],
                              'slack_title_template'
                            )
                          }
                        />

                        <IntegrationTemplateBlock
                          label={'Message'}
                          renderInput={() => (
                            <div className={cx('input', 'input--long')}>
                              <MonacoJinja2Editor
                                value={templates['slack_message_template'] || ''}
                                disabled={true}
                                height={MONACO_INPUT_HEIGHT_TALL}
                                data={templates}
                                showLineNumbers={false}
                                monacoOptions={MONACO_OPTIONS}
                              />
                            </div>
                          )}
                          onEdit={() =>
                            this.openEditTemplateModal(
                              'Slack message',
                              templates['slack_message_template'],
                              'slack_message_template'
                            )
                          }
                        />

                        <IntegrationTemplateBlock
                          label={'Image'}
                          renderInput={() => (
                            <div className={cx('input', 'input--long')}>
                              <MonacoJinja2Editor
                                value={templates['slack_image_template'] || ''}
                                disabled={true}
                                height={MONACO_INPUT_HEIGHT_SMALL}
                                data={templates}
                                showLineNumbers={false}
                                monacoOptions={MONACO_OPTIONS}
                              />
                            </div>
                          )}
                          onEdit={() =>
                            this.openEditTemplateModal(
                              'Slack image',
                              templates['slack_image_template'],
                              'slack_image_template'
                            )
                          }
                        />
                      </VerticalGroup>
                    </IntegrationBlockItem>

                    <IntegrationBlockItem>
                      <VerticalGroup>
                        <Text type={'primary'}>Telegram</Text>
                        <IntegrationTemplateBlock
                          label={'Title'}
                          renderInput={() => (
                            <div className={cx('input', 'input--long')}>
                              <MonacoJinja2Editor
                                value={templates['telegram_title_template'] || ''}
                                disabled={true}
                                height={MONACO_INPUT_HEIGHT_SMALL}
                                data={templates}
                                showLineNumbers={false}
                                monacoOptions={MONACO_OPTIONS}
                              />
                            </div>
                          )}
                          onEdit={() =>
                            this.openEditTemplateModal(
                              'Telegram title',
                              templates['telegram_title_template'],
                              'telegram_title_template'
                            )
                          }
                        />

                        <IntegrationTemplateBlock
                          label={'Message'}
                          renderInput={() => (
                            <div className={cx('input', 'input--long')}>
                              <MonacoJinja2Editor
                                value={templates['telegram_message_template'] || ''}
                                disabled={true}
                                height={MONACO_INPUT_HEIGHT_TALL}
                                data={templates}
                                showLineNumbers={false}
                                monacoOptions={MONACO_OPTIONS}
                              />
                            </div>
                          )}
                          onEdit={() =>
                            this.openEditTemplateModal(
                              'Telegram message',
                              templates['telegram_message_template'],
                              'telegram_message_template'
                            )
                          }
                        />

                        <IntegrationTemplateBlock
                          label={'Image'}
                          renderInput={() => (
                            <div className={cx('input', 'input--long')}>
                              <MonacoJinja2Editor
                                value={templates['telegram_image_url_template'] || ''}
                                disabled={true}
                                height={MONACO_INPUT_HEIGHT_SMALL}
                                data={templates}
                                showLineNumbers={false}
                                monacoOptions={MONACO_OPTIONS}
                              />
                            </div>
                          )}
                          onEdit={() =>
                            this.openEditTemplateModal(
                              'Telegram image',
                              templates['telegram_image_url_template'],
                              'telegram_image_url_template'
                            )
                          }
                        />
                      </VerticalGroup>
                    </IntegrationBlockItem>

                    <IntegrationBlockItem>
                      <VerticalGroup>
                        <Text type={'primary'}>Email</Text>
                        <IntegrationTemplateBlock
                          label={'Title'}
                          renderInput={() => (
                            <div className={cx('input', 'input--long')}>
                              <MonacoJinja2Editor
                                value={templates['email_title_template'] || ''}
                                disabled={true}
                                height={MONACO_INPUT_HEIGHT_SMALL}
                                data={templates}
                                showLineNumbers={false}
                                monacoOptions={MONACO_OPTIONS}
                              />
                            </div>
                          )}
                          onEdit={() =>
                            this.openEditTemplateModal(
                              'Email title',
                              templates['email_title_template'],
                              'email_title_template'
                            )
                          }
                        />

                        <IntegrationTemplateBlock
                          label={'Message'}
                          renderInput={() => (
                            <div className={cx('input', 'input--long')}>
                              <MonacoJinja2Editor
                                value={templates['email_message_template'] || ''}
                                disabled={true}
                                height={MONACO_INPUT_HEIGHT_TALL}
                                data={templates}
                                showLineNumbers={false}
                                monacoOptions={MONACO_OPTIONS}
                              />
                            </div>
                          )}
                          onEdit={() =>
                            this.openEditTemplateModal(
                              'Email message',
                              templates['email_message_template'],
                              'email_message_template'
                            )
                          }
                        />
                      </VerticalGroup>
                    </IntegrationBlockItem>

                    <IntegrationBlockItem>
                      <VerticalGroup>
                        <Text type={'secondary'}>By default alert groups rendered based on Web templates.</Text>
                        <Text type={'secondary'}>
                          Customise how they rendered in SMS, Phone Calls, Mobile App, Slack, Telegram, MS Teams{' '}
                        </Text>

                        <div className={cx('customise-button')}>
                          <ButtonCascader
                            variant="secondary"
                            onChange={(_value) => {
                              console.log('VALUE', _value);
                            }}
                            options={this.getTemplatesList()}
                            icon="plus"
                            value={undefined}
                            buttonProps={{ size: 'sm' }}
                          >
                            Customise templates
                          </ButtonCascader>
                        </div>
                      </VerticalGroup>
                    </IntegrationBlockItem>
                  </div>
                }
              />

              <div className={cx('routesSection')}>
                <VerticalGroup spacing="md">
                  <div className="thin-line-break" />
                  <Text type={'primary'}>Routes</Text>
                  <Button variant={'primary'} onClick={() => {}}>
                    Add route
                  </Button>
                </VerticalGroup>
              </div>

              {this.renderRoutes}
            </IntegrationCollapsibleTreeView>

            <IntegrationSendDemoPayloadModal
              alertReceiveChannel={alertReceiveChannel}
              isOpen={isDemoModalOpen}
              onCancel={() => this.setState({ isDemoModalOpen: false })}
            />
            {isEditTemplateModalOpen && (
              <IntegrationTemplate
                id={id}
                onHide={() => {
                  this.setState({
                    isEditTemplateModalOpen: undefined,
                  });
                }}
                onUpdateTemplates={this.onUpdateTemplatesCallback}
                template={selectedTemplate}
              />
            )}
          </div>
        )}
      </PageErrorHandlingWrapper>
    );
  }

  renderRoutes = () => {
    const {
      store: { alertReceiveChannelStore },
      match: {
        params: { id },
      },
    } = this.props;

    const templates = alertReceiveChannelStore.templates[id];

    return Object.keys(alertReceiveChannelStore.channelFilters).map((channelFilterId, channelFilterIndex) => (
      <IntegrationRouteDisplay
        channelFilter={alertReceiveChannelStore.channelFilters[channelFilterId]}
        routeIndex={channelFilterIndex}
        templates={templates}
      />
    ));
  };

  handleSlackChannelChange = () => {};

  onUpdateTemplatesCallback = (data) => {
    const {
      store,
      match: {
        params: { id },
      },
    } = this.props;
    store.alertReceiveChannelStore
      .saveTemplates(id, data)
      .then(() => {
        openNotification('Alert templates are successfully updated');
        // if (onUpdateTemplates) {
        //   onUpdateTemplates();
        // }
      })
      .catch((err) => {
        if (err.response?.data?.length > 0) {
          openErrorNotification(err.response.data);
        } else {
          openErrorNotification(err.message);
        }
      });
  };

  getTemplatesList = (): CascaderOption[] => INTEGRATION_TEMPLATES_LIST;

  openEditTemplateModal = (templateNameForWeb, templateBody, templateName) => {
    this.setState({ isEditTemplateModalOpen: true });
    const template: TemplateForEdit = { displayName: templateNameForWeb, body: templateBody, name: templateName };
    this.setState({ selectedTemplate: template });
  };

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

        <HorizontalGroup justify={'flex-end'} spacing={'md'}>
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
    return JSON.stringify(INTEGRATION_DEMO_PAYLOAD, null, 4);
  }
};

export default withRouter(withMobXProviderContext(Integration2));
