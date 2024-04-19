import React, { useState, SyntheticEvent } from 'react';

import { LabelTag } from '@grafana/labels';
import {
  Button,
  HorizontalGroup,
  Icon,
  IconButton,
  LoadingPlaceholder,
  RadioButtonGroup,
  TextArea,
  ToolbarButton,
  VerticalGroup,
  Field,
  Modal,
  Tooltip,
  Divider,
} from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import moment from 'moment-timezone';
import CopyToClipboard from 'react-copy-to-clipboard';
import Emoji from 'react-emoji-render';
import { RouteComponentProps, withRouter } from 'react-router-dom';
import reactStringReplace from 'react-string-replace';
import { OnCallPluginExtensionPoints } from 'types';

import errorSVG from 'assets/img/error.svg';
import { Collapse } from 'components/Collapse/Collapse';
import { ExtensionLinkDropdown } from 'components/ExtensionLinkMenu/ExtensionLinkDropdown';
import { Block } from 'components/GBlock/Block';
import { IntegrationLogo } from 'components/IntegrationLogo/IntegrationLogo';
import { PageErrorHandlingWrapper, PageBaseState } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper';
import {
  getWrongTeamResponseInfo,
  initErrorDataState,
} from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper.helpers';
import { PluginLink } from 'components/PluginLink/PluginLink';
import { SourceCode } from 'components/SourceCode/SourceCode';
import { Text } from 'components/Text/Text';
import { TooltipBadge } from 'components/TooltipBadge/TooltipBadge';
import { AddResponders } from 'containers/AddResponders/AddResponders';
import { prepareForUpdate } from 'containers/AddResponders/AddResponders.helpers';
import { UserResponder } from 'containers/AddResponders/AddResponders.types';
import { AttachIncidentForm } from 'containers/AttachIncidentForm/AttachIncidentForm';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { AlertReceiveChannelHelper } from 'models/alert_receive_channel/alert_receive_channel.helpers';
import { AlertGroupHelper } from 'models/alertgroup/alertgroup.helpers';
import { AlertAction, TimeLineItem, TimeLineRealm, GroupedAlert } from 'models/alertgroup/alertgroup.types';
import { ResolutionNoteSourceTypesToDisplayName } from 'models/resolution_note/resolution_note.types';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { IncidentDropdown } from 'pages/incidents/parts/IncidentDropdown';
import { AppFeature } from 'state/features';
import { PageProps, WithStoreProps } from 'state/types';
import { useStore } from 'state/useStore';
import { withMobXProviderContext } from 'state/withStore';
import { UserActions } from 'utils/authorization/authorization';
import { INTEGRATION_SERVICENOW, PLUGIN_ROOT } from 'utils/consts';
import { sanitize } from 'utils/sanitize';
import { parseURL } from 'utils/url';
import { openNotification } from 'utils/utils';

import { getActionButtons } from './Incident.helpers';
import styles from './Incident.module.scss';

const cx = cn.bind(styles);
const INTEGRATION_NAME_LENGTH_LIMIT = 30;

interface IncidentPageProps extends WithStoreProps, PageProps, RouteComponentProps<{ id: string }> {}

interface IncidentPageState extends PageBaseState {
  showIntegrationSettings?: boolean;
  showAttachIncidentForm?: boolean;
  timelineFilter: string;
  resolutionNoteText: string;
}

@observer
class _IncidentPage extends React.Component<IncidentPageProps, IncidentPageState> {
  state: IncidentPageState = {
    timelineFilter: 'all',
    resolutionNoteText: '',
    errorData: initErrorDataState(),
  };

  componentDidMount() {
    const { store } = this.props;

    this.update();

    store.alertGroupStore.fetchSilenceOptions();
  }

  componentWillUnmount(): void {
    this.props.store.setPageTitle('');
  }

  componentDidUpdate(prevProps: IncidentPageProps) {
    if (this.props.match.params.id !== prevProps.match.params.id) {
      this.update();
    }
  }

  update = async () => {
    this.setState({ errorData: initErrorDataState() }); // reset wrong team error to false

    const {
      store,
      match: {
        params: { id },
      },
    } = this.props;

    try {
      await store.alertGroupStore.getAlert(id);
    } catch (error) {
      this.setState({ errorData: { ...getWrongTeamResponseInfo(error) } });
    }
  };

  render() {
    const {
      store,
      query: { cursor, start, perpage },
      match: {
        params: { id },
      },
    } = this.props;

    const { errorData, showIntegrationSettings, showAttachIncidentForm } = this.state;
    const { isNotFoundError, isWrongTeamError, isUnknownError } = errorData;
    const { alerts } = store.alertGroupStore;

    const incident = alerts.get(id);

    if (isUnknownError) {
      return (
        <AlertGroupStub
          buttons={getActionButtons(
            incident,
            {
              onResolve: this.getOnActionButtonClick(id, AlertAction.Resolve),
              onUnacknowledge: this.getOnActionButtonClick(id, AlertAction.unAcknowledge),
              onUnresolve: this.getOnActionButtonClick(id, AlertAction.unResolve),
              onAcknowledge: this.getOnActionButtonClick(id, AlertAction.Acknowledge),
              onSilence: this.getSilenceClickHandler(id),
              onUnsilence: this.getUnsilenceClickHandler(id),
            },
            true
          )}
        />
      );
    }

    if (!incident && !isNotFoundError && !isWrongTeamError) {
      return (
        <div className={cx('root')}>
          <LoadingPlaceholder text="Loading Alert Group..." />
        </div>
      );
    }

    return (
      <PageErrorHandlingWrapper errorData={errorData} objectName="alert group" pageName="incidents">
        {() => (
          <div className={cx('root')}>
            {errorData.isNotFoundError ? (
              <div className={cx('not-found')}>
                <VerticalGroup spacing="lg" align="center">
                  <Text.Title level={1}>404</Text.Title>
                  <Text.Title level={4}>Alert group not found</Text.Title>
                  <PluginLink query={{ page: 'alert-groups', cursor, start, perpage }}>
                    <Button variant="secondary" icon="arrow-left" size="md">
                      Go to Alert Groups page
                    </Button>
                  </PluginLink>
                </VerticalGroup>
              </div>
            ) : (
              <>
                {this.renderHeader()}
                <div className={cx('content')}>
                  <div className={cx('column')}>
                    <Incident incident={incident} datetimeReference={this.getIncidentDatetimeReference(incident)} />
                    <GroupedIncidentsList
                      id={incident.pk}
                      getIncidentDatetimeReference={this.getIncidentDatetimeReference}
                    />
                    <AttachedIncidentsList id={incident.pk} getUnattachClickHandler={this.getUnattachClickHandler} />
                  </div>
                  <div className={cx('column')}>
                    <VerticalGroup style={{ display: 'block' }}>
                      {(!incident.resolved || incident?.paged_users?.length > 0) && (
                        <AddResponders
                          mode="update"
                          hideAddResponderButton={incident.resolved}
                          existingPagedUsers={incident.paged_users}
                          onAddNewParticipant={this.handleAddUserResponder}
                          generateRemovePreviouslyPagedUserCallback={this.handlePagedUserRemove}
                        />
                      )}
                      {this.renderTimeline()}
                    </VerticalGroup>
                  </div>
                </div>
                {showIntegrationSettings && (
                  <Modal
                    isOpen
                    title="Edit template"
                    onDismiss={() =>
                      this.setState({
                        showIntegrationSettings: undefined,
                      })
                    }
                  >
                    <Text>
                      Please go to{' '}
                      <PluginLink
                        query={{
                          page: 'integrations',
                          id: incident.alert_receive_channel.id,
                          // tab: IntegrationSettingsTab.Templates,
                        }}
                      >
                        Integrations
                      </PluginLink>{' '}
                      to edit this template
                    </Text>
                  </Modal>
                )}
                {showAttachIncidentForm && (
                  <AttachIncidentForm
                    id={id}
                    onHide={() => {
                      this.setState({
                        showAttachIncidentForm: false,
                      });
                    }}
                    onUpdate={this.update}
                  />
                )}
              </>
            )}
          </div>
        )}
      </PageErrorHandlingWrapper>
    );
  }

  handlePagedUserRemove = (userId: ApiSchemas['User']['pk']) => {
    return async () => {
      const {
        match: {
          params: { id: alertId },
        },
      } = this.props;

      await AlertGroupHelper.unpageUser(alertId, userId);

      this.update();
    };
  };

  renderHeader = () => {
    const {
      store,
      query,
      match: {
        params: { id },
      },
    } = this.props;
    const { alerts } = store.alertGroupStore;
    const incident = alerts.get(id);
    const integration = AlertReceiveChannelHelper.getIntegrationSelectOption(
      store.alertReceiveChannelStore,
      incident.alert_receive_channel
    );
    const showLinkTo = !incident.dependent_alert_groups.length && !incident.root_alert_group && !incident.resolved;
    const integrationNameWithEmojies = <Emoji text={incident.alert_receive_channel.verbal_name} />;
    const sourceLink = incident?.render_for_web?.source_link;
    const isServiceNow = Boolean(incident?.external_urls?.find((el) => el.integration_type === INTEGRATION_SERVICENOW));

    return (
      <Block className={cx('block')}>
        <VerticalGroup>
          <HorizontalGroup justify="space-between">
            <HorizontalGroup className={cx('title')}>
              <PluginLink query={{ page: 'alert-groups', ...query }}>
                <IconButton aria-label="Go Back" name="arrow-left" size="xl" />
              </PluginLink>
              {/* @ts-ignore*/}
              <HorizontalGroup align="baseline">
                <Text.Title level={3} data-testid="incident-title">
                  {store.pageTitle}
                </Text.Title>
                {incident.root_alert_group && (
                  <Text type="secondary">
                    Attached to{' '}
                    <PluginLink query={{ page: 'alert-groups', id: incident.root_alert_group.pk }}>
                      #{incident.root_alert_group.inside_organization_number}{' '}
                      {incident.root_alert_group.render_for_web.title}
                    </PluginLink>{' '}
                    <WithPermissionControlTooltip userAction={UserActions.AlertGroupsWrite}>
                      <Button variant="secondary" onClick={() => this.getUnattachClickHandler(incident.pk)} size="sm">
                        Unattach
                      </Button>
                    </WithPermissionControlTooltip>
                  </Text>
                )}
              </HorizontalGroup>
            </HorizontalGroup>
            <HorizontalGroup align="center">
              <Text>
                {showLinkTo && (
                  <IconButton
                    name="code-branch"
                    onClick={this.showAttachIncidentForm}
                    tooltip="Attach to another Alert Group"
                    className={cx('title-icon')}
                  />
                )}
                <a href={incident.slack_permalink} target="_blank" rel="noreferrer">
                  <IconButton name="slack" tooltip="View in Slack" className={cx('title-icon')} />
                </a>
                <CopyToClipboard
                  text={window.location.href}
                  onCopy={() => {
                    openNotification('Link copied');
                  }}
                >
                  <IconButton name="copy" tooltip="Copy link" className={cx('title-icon')} />
                </CopyToClipboard>
              </Text>
            </HorizontalGroup>
          </HorizontalGroup>
          <div className={cx('info-row')}>
            <HorizontalGroup>
              <div className={cx('status-tag-container')}>
                <IncidentDropdown
                  alert={incident}
                  onResolve={this.getOnActionButtonClick(incident.pk, AlertAction.Resolve)}
                  onUnacknowledge={this.getOnActionButtonClick(incident.pk, AlertAction.unAcknowledge)}
                  onUnresolve={this.getOnActionButtonClick(incident.pk, AlertAction.unResolve)}
                  onAcknowledge={this.getOnActionButtonClick(incident.pk, AlertAction.Acknowledge)}
                  onSilence={this.getSilenceClickHandler(incident.pk)}
                  onUnsilence={this.getUnsilenceClickHandler(incident.pk)}
                />
              </div>

              {Boolean(store.hasFeature(AppFeature.Labels) && incident.labels.length) && (
                <TooltipBadge
                  borderType="secondary"
                  icon="tag-alt"
                  addPadding
                  text={incident.labels.length}
                  tooltipContent={
                    <VerticalGroup spacing="sm">
                      {incident.labels.map((label) => (
                        <LabelTag label={label.key.name} value={label.value.name} key={label.key.id} />
                      ))}
                    </VerticalGroup>
                  }
                />
              )}

              {integration && (
                <HorizontalGroup>
                  <PluginLink
                    disabled={incident.alert_receive_channel.deleted}
                    query={{ page: 'integrations', id: incident.alert_receive_channel.id }}
                  >
                    <Button
                      disabled={incident.alert_receive_channel.deleted}
                      variant="secondary"
                      fill="outline"
                      size="sm"
                      className={cx('label-button')}
                    >
                      <Tooltip
                        placement="top"
                        content={
                          incident.alert_receive_channel.verbal_name.length > INTEGRATION_NAME_LENGTH_LIMIT
                            ? integrationNameWithEmojies
                            : 'Go to Integration'
                        }
                      >
                        <div className={cx('label-button-text', 'source-name')}>
                          <div className={cx('integration-logo')}>
                            <IntegrationLogo integration={integration} scale={0.08} />
                          </div>
                          <div className={cx('label-button-text')}>{integrationNameWithEmojies}</div>
                        </div>
                      </Tooltip>
                    </Button>
                  </PluginLink>

                  {isServiceNow && (
                    <Button variant="secondary" fill="outline" size="sm" className={cx('label-button')}>
                      <HorizontalGroup spacing="xs">
                        <Icon name="exchange-alt" />
                        <span>Service Now</span>
                      </HorizontalGroup>
                    </Button>
                  )}

                  <Tooltip
                    placement="top"
                    content={
                      sourceLink === null
                        ? `The integration template Source Link is empty`
                        : parseURL(sourceLink) === ''
                        ? 'The Integration template Source Link is invalid'
                        : 'Go to source'
                    }
                  >
                    <a href={parseURL(sourceLink) || undefined} target="_blank" rel="noreferrer">
                      <Button
                        variant="secondary"
                        fill="outline"
                        size="sm"
                        disabled={sourceLink === null || parseURL(sourceLink) === ''}
                        className={cx('label-button')}
                        icon="external-link-alt"
                      >
                        Source
                      </Button>
                    </a>
                  </Tooltip>
                </HorizontalGroup>
              )}
            </HorizontalGroup>
          </div>
          <HorizontalGroup justify="space-between" className={cx('buttons-row')}>
            <HorizontalGroup>
              {getActionButtons(incident, {
                onResolve: this.getOnActionButtonClick(incident.pk, AlertAction.Resolve),
                onUnacknowledge: this.getOnActionButtonClick(incident.pk, AlertAction.unAcknowledge),
                onUnresolve: this.getOnActionButtonClick(incident.pk, AlertAction.unResolve),
                onAcknowledge: this.getOnActionButtonClick(incident.pk, AlertAction.Acknowledge),
                onSilence: this.getSilenceClickHandler(incident.pk),
                onUnsilence: this.getUnsilenceClickHandler(incident.pk),
              })}
              <ExtensionLinkDropdown
                incident={incident}
                extensionPointId={OnCallPluginExtensionPoints.AlertGroupAction}
                declareIncidentLink={incident.declare_incident_link}
                grafanaIncidentId={incident.grafana_incident_id}
              />
            </HorizontalGroup>

            <Button
              disabled={incident.alert_receive_channel.deleted}
              variant="secondary"
              icon="edit"
              onClick={this.showIntegrationSettings}
            >
              Edit templates
            </Button>
          </HorizontalGroup>
        </VerticalGroup>
      </Block>
    );
  };

  handleAddUserResponder = async (user: Omit<UserResponder, 'type'>) => {
    const {
      store,
      match: {
        params: { id: alertId },
      },
    } = this.props;

    await store.directPagingStore.updateAlertGroup(alertId, prepareForUpdate([user]));

    this.update();
  };

  showIntegrationSettings = () => {
    this.setState({ showIntegrationSettings: true });
  };

  showAttachIncidentForm = () => {
    this.setState({ showAttachIncidentForm: true });
  };

  getUnattachClickHandler = async (pk: ApiSchemas['AlertGroup']['pk']) => {
    await AlertGroupHelper.unattachAlert(pk);
    this.update();
  };

  renderTimeline = () => {
    const {
      store,
      history,
      match: {
        params: { id },
      },
    } = this.props;

    const incident = store.alertGroupStore.alerts.get(id);

    if (!incident.render_after_resolve_report_json) {
      return null;
    }

    const timeline = this.filterTimeline(incident.render_after_resolve_report_json);
    const { timelineFilter, resolutionNoteText } = this.state;
    const isResolutionNoteTextEmpty = resolutionNoteText === '';
    return (
      <Block bordered>
        <Text.Title type="primary" level={4} className={cx('timeline-title')}>
          Timeline
        </Text.Title>
        <RadioButtonGroup
          className={cx('timeline-filter')}
          options={[
            { label: 'Show full timeline', value: 'all' },
            { label: 'Resolution notes only', value: TimeLineRealm.ResolutionNote },
          ]}
          value={timelineFilter}
          onChange={(value) => {
            this.setState({ timelineFilter: value });
          }}
        />
        <ul className={cx('timeline')} data-testid="incident-timeline-list">
          {timeline.map((item: TimeLineItem, idx: number) => (
            <li key={idx} className={cx('timeline-item')}>
              <HorizontalGroup align="flex-start">
                <div className={cx('timeline-icon-background', { blue: item.realm === TimeLineRealm.ResolutionNote })}>
                  {this.renderTimelineItemIcon(item.realm)}
                </div>
                <VerticalGroup spacing="none">
                  {item.realm === TimeLineRealm.ResolutionNote && (
                    <Text type="secondary" size="small">
                      {item.author && item.author.username} via{' '}
                      {ResolutionNoteSourceTypesToDisplayName[item.type] || 'Web'}
                    </Text>
                  )}
                  <Text type="primary">
                    {reactStringReplace(item.action, /\{\{([^}]+)\}\}/g, this.getPlaceholderReplaceFn(item, history))}
                  </Text>
                  <Text type="secondary" size="small">
                    {moment(item.created_at).format('MMM DD, YYYY HH:mm:ss Z')}
                  </Text>
                </VerticalGroup>
              </HorizontalGroup>
            </li>
          ))}
        </ul>
        <Field
          label="Leave a resolution note"
          description="Will also show up in the thread of the Alert Group in Slack"
        >
          <TextArea
            value={resolutionNoteText}
            onChange={(e: any) => this.setState({ resolutionNoteText: e.target.value })}
          />
        </Field>
        <WithPermissionControlTooltip userAction={UserActions.AlertGroupsWrite}>
          <ToolbarButton
            icon="plus"
            variant="primary"
            onClick={this.handleCreateResolutionNote}
            disabled={isResolutionNoteTextEmpty}
          >
            Add resolution note
          </ToolbarButton>
        </WithPermissionControlTooltip>
      </Block>
    );
  };

  filterTimeline = (timeline: ApiSchemas['AlertGroup']['render_after_resolve_report_json']) => {
    if (this.state.timelineFilter === 'all') {
      return timeline;
    } else {
      return timeline.filter((item) => item.realm === this.state.timelineFilter);
    }
  };

  renderTimelineItemIcon = (realm: TimeLineRealm) => {
    switch (realm) {
      case TimeLineRealm.UserNotification:
        return <Icon size="lg" name="user" />;
      case TimeLineRealm.AlertGroup:
        return <Icon size="lg" name="bell" />;
      case TimeLineRealm.ResolutionNote:
        return <Icon size="lg" name="envelope" />;
    }
  };

  handleCreateResolutionNote = async () => {
    const {
      store,
      match: {
        params: { id },
      },
    } = this.props;

    const { resolutionNoteText } = this.state;

    await store.resolutionNotesStore.createResolutionNote(id, resolutionNoteText);
    this.setState({ resolutionNoteText: '' });
    await this.update();
  };

  getPlaceholderReplaceFn = (entity: any, history) => {
    return (match: string) => {
      switch (match) {
        case 'author':
          return (
            <span
              onClick={() => history.push(`${PLUGIN_ROOT}/users/${entity?.author?.pk}`)}
              style={{ textDecoration: 'underline', cursor: 'pointer' }}
            >
              {entity.author?.username}
            </span>
          );
        default:
          return '{{' + match + '}}';
      }
    };
  };

  getOnActionButtonClick = (incidentId: ApiSchemas['AlertGroup']['pk'], action: AlertAction) => {
    const { store } = this.props;

    return (e: SyntheticEvent) => {
      e.stopPropagation();

      return store.alertGroupStore.doIncidentAction(incidentId, action);
    };
  };

  getSilenceClickHandler = (incidentId: ApiSchemas['AlertGroup']['pk']) => {
    const { store } = this.props;

    return (value: number) => {
      return store.alertGroupStore.doIncidentAction(incidentId, AlertAction.Silence, value);
    };
  };

  getUnsilenceClickHandler = (incidentId: ApiSchemas['AlertGroup']['pk']) => {
    const { store } = this.props;

    return (event: any) => {
      event.stopPropagation();

      return store.alertGroupStore.doIncidentAction(incidentId, AlertAction.unSilence);
    };
  };

  getIncidentDatetimeReference = (incident: ApiSchemas['AlertGroup'] | GroupedAlert): string => {
    let datetimeReference;
    if ((incident as ApiSchemas['AlertGroup']).last_alert_at || incident.created_at) {
      const m = moment((incident as ApiSchemas['AlertGroup']).last_alert_at || incident.created_at);
      datetimeReference = `(${m.fromNow()}, ${m.toString()})`;
    }

    return datetimeReference;
  };
}

function Incident({ incident }: { incident: ApiSchemas['AlertGroup']; datetimeReference: string }) {
  return (
    <div key={incident.pk} className={cx('incident')}>
      <div
        className={cx('message')}
        dangerouslySetInnerHTML={{
          __html: sanitize(incident.render_for_web.message),
        }}
        data-testid="incident-message"
      />
      {incident.render_for_web.image_url && <img className={cx('image')} src={incident.render_for_web.image_url} />}
    </div>
  );
}

function GroupedIncidentsList({
  id,
  getIncidentDatetimeReference,
}: {
  id: string;
  getIncidentDatetimeReference: (incident: GroupedAlert) => string;
}) {
  const store = useStore();
  const incident = store.alertGroupStore.alerts.get(id);

  const alerts = incident.alerts;
  if (!alerts) {
    return null;
  }

  const latestAlert = alerts[0];
  const latestAlertMoment = moment(latestAlert.created_at);

  return (
    <Collapse
      headerWithBackground
      className={cx('collapse')}
      isOpen={false}
      label={
        <HorizontalGroup wrap>
          <Text>{incident.alerts_count} Grouped Alerts</Text>
          <Text type="secondary">latest {latestAlertMoment.fromNow()},</Text>
          <Text type="secondary">{latestAlertMoment.format('MMM DD, YYYY HH:mm:ss Z').toString()}</Text>
        </HorizontalGroup>
      }
      contentClassName={cx('incidents-content')}
    >
      {alerts.map((alert) => (
        <GroupedIncident key={alert.id} incident={alert} datetimeReference={getIncidentDatetimeReference(alert)} />
      ))}
    </Collapse>
  );
}

function GroupedIncident({ incident, datetimeReference }: { incident: GroupedAlert; datetimeReference: string }) {
  const [incidentRawResponse, setIncidentRawResponse] = useState<{ id: string; raw_request_data: any }>(undefined);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const payloadJSON = isModalOpen ? JSON.stringify(incidentRawResponse.raw_request_data, null, 4) : undefined;

  return (
    <>
      {isModalOpen && (
        <Modal onDismiss={() => setIsModalOpen(false)} closeOnEscape isOpen={isModalOpen} title="Alert Payload">
          <div className={cx('payload-subtitle')}>
            <HorizontalGroup>
              <Text type="secondary">
                {incident.render_for_web.title} - {datetimeReference}
              </Text>
            </HorizontalGroup>
          </div>
          <VerticalGroup>
            <SourceCode showCopyToClipboard={false}>{payloadJSON}</SourceCode>
            <HorizontalGroup justify={'flex-end'}>
              <CopyToClipboard
                text={payloadJSON}
                onCopy={() => {
                  openNotification('Copied!');
                }}
              >
                <Button className={cx('button')} variant="primary" icon="copy">
                  Copy to Clipboard
                </Button>
              </CopyToClipboard>
            </HorizontalGroup>
          </VerticalGroup>
        </Modal>
      )}

      <div key={incident.id}>
        <div className={cx('incident-row')}>
          <div className={cx('incident-row-left')}>
            <HorizontalGroup wrap justify={'flex-start'}>
              <Text.Title type="secondary" level={4}>
                {incident.render_for_web.title}
              </Text.Title>
              <Text type="secondary">{datetimeReference}</Text>
            </HorizontalGroup>
          </div>
          <div className={cx('incident-row-right')}>
            <HorizontalGroup wrap={false} justify={'flex-end'}>
              <Tooltip placement="top" content="Alert Payload">
                <IconButton aria-label="Alert Payload" name="arrow" onClick={() => openIncidentResponse(incident)} />
              </Tooltip>
            </HorizontalGroup>
          </div>
        </div>
        <Text type="secondary">
          <div
            className={cx('message')}
            dangerouslySetInnerHTML={{
              __html: sanitize(incident.render_for_web.message),
            }}
          />
        </Text>
        {incident.render_for_web.image_url && <img className={cx('image')} src={incident.render_for_web.image_url} />}
      </div>
    </>
  );

  async function openIncidentResponse(incident: GroupedAlert) {
    const currentIncidentRawResponse = await AlertGroupHelper.getPayloadForIncident(incident.id);
    setIncidentRawResponse(currentIncidentRawResponse);
    setIsModalOpen(true);
  }
}

function AttachedIncidentsList({
  id,
  getUnattachClickHandler,
}: {
  id: string;
  getUnattachClickHandler(pk: string): void;
}) {
  const store = useStore();
  const incident = store.alertGroupStore.alerts.get(id);

  if (!incident.dependent_alert_groups.length) {
    return null;
  }

  const alerts = incident.dependent_alert_groups;

  return (
    <Collapse
      headerWithBackground
      className={cx('collapse')}
      isOpen
      label={<HorizontalGroup wrap>{incident.dependent_alert_groups.length} Attached Alert Groups</HorizontalGroup>}
      contentClassName={cx('incidents-content')}
    >
      {alerts.map((incident) => {
        return (
          <HorizontalGroup key={incident.pk} justify={'space-between'}>
            <PluginLink query={{ page: 'alert-groups', id: incident.pk }}>
              #{incident.inside_organization_number} {incident.render_for_web.title}
            </PluginLink>
            <WithPermissionControlTooltip userAction={UserActions.AlertGroupsWrite}>
              <Button size="sm" onClick={() => getUnattachClickHandler(incident.pk)} variant="secondary">
                Unattach
              </Button>
            </WithPermissionControlTooltip>
          </HorizontalGroup>
        );
      })}
    </Collapse>
  );
}

const AlertGroupStub = ({ buttons }: { buttons: React.ReactNode }) => {
  return (
    <div className={cx('alert-group-stub')}>
      <VerticalGroup align="center" spacing="md">
        <img src={errorSVG} alt="" />
        <Text.Title level={3}>An unexpected error happened</Text.Title>
        <Text type="secondary">
          OnCall is not able to receive any information about the current Alert Group. It's unknown if it's firing,
          acknowledged, silenced, or resolved.
        </Text>
        <div className={cx('alert-group-stub-divider')}>
          <Divider />
        </div>
        <Text type="secondary">Meanwhile, you could try changing the status of this Alert Group:</Text>
        <HorizontalGroup wrap justify="center">
          {buttons}
        </HorizontalGroup>
      </VerticalGroup>
    </div>
  );
};

export const IncidentPage = withRouter(withMobXProviderContext(_IncidentPage));
