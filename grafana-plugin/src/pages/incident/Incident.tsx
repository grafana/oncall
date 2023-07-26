import React, { useState, SyntheticEvent } from 'react';

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
} from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import moment from 'moment-timezone';
import CopyToClipboard from 'react-copy-to-clipboard';
import Emoji from 'react-emoji-render';
import { RouteComponentProps, withRouter } from 'react-router-dom';
import reactStringReplace from 'react-string-replace';

import Collapse from 'components/Collapse/Collapse';
import Block from 'components/GBlock/Block';
import IntegrationLogo from 'components/IntegrationLogo/IntegrationLogo';
import PageErrorHandlingWrapper, { PageBaseState } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper';
import {
  getWrongTeamResponseInfo,
  initErrorDataState,
} from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper.helpers';
import { PluginBridge, SupportedPlugin } from 'components/PluginBridge/PluginBridge';
import PluginLink from 'components/PluginLink/PluginLink';
import SourceCode from 'components/SourceCode/SourceCode';
import Text from 'components/Text/Text';
import AttachIncidentForm from 'containers/AttachIncidentForm/AttachIncidentForm';
import EscalationVariants from 'containers/EscalationVariants/EscalationVariants';
import { prepareForEdit, prepareForUpdate } from 'containers/EscalationVariants/EscalationVariants.helpers';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import {
  Alert as AlertType,
  Alert,
  AlertAction,
  TimeLineItem,
  TimeLineRealm,
  GroupedAlert,
} from 'models/alertgroup/alertgroup.types';
import { ResolutionNoteSourceTypesToDisplayName } from 'models/resolution_note/resolution_note.types';
import { User } from 'models/user/user.types';
import { IncidentDropdown } from 'pages/incidents/parts/IncidentDropdown';
import { PageProps, WithStoreProps } from 'state/types';
import { useStore } from 'state/useStore';
import { withMobXProviderContext } from 'state/withStore';
import { openNotification } from 'utils';
import { UserActions } from 'utils/authorization';
import { PLUGIN_ROOT } from 'utils/consts';
import sanitize from 'utils/sanitize';

import { getActionButtons } from './Incident.helpers';
import styles from './Incident.module.scss';
import PagedUsers from './parts/PagedUsers';

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
class IncidentPage extends React.Component<IncidentPageProps, IncidentPageState> {
  state: IncidentPageState = {
    timelineFilter: 'all',
    resolutionNoteText: '',
    errorData: initErrorDataState(),
  };

  componentDidMount() {
    const { store } = this.props;

    this.update();

    store.alertGroupStore.updateSilenceOptions();
  }

  componentDidUpdate(prevProps: IncidentPageProps) {
    if (this.props.match.params.id !== prevProps.match.params.id) {
      this.update();
    }
  }

  update = () => {
    this.setState({ errorData: initErrorDataState() }); // reset wrong team error to false

    const {
      store,
      match: {
        params: { id },
      },
    } = this.props;

    store.alertGroupStore
      .getAlert(id)
      .catch((error) => this.setState({ errorData: { ...getWrongTeamResponseInfo(error) } }));
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
    const { isNotFoundError, isWrongTeamError } = errorData;
    // const { alertReceiveChannelStore } = store;
    const { alerts } = store.alertGroupStore;

    const incident = alerts.get(id);

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
                      disabled={incident.is_restricted}
                      getIncidentDatetimeReference={this.getIncidentDatetimeReference}
                    />
                    <AttachedIncidentsList id={incident.pk} getUnattachClickHandler={this.getUnattachClickHandler} />
                  </div>
                  <div className={cx('column')}>
                    <VerticalGroup>
                      <PagedUsers
                        pagedUsers={incident.paged_users}
                        onRemove={this.handlePagedUserRemove}
                        disabled={incident.is_restricted}
                      />
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

  handlePagedUserRemove = async (userId: User['pk']) => {
    const {
      store,
      match: {
        params: { id: alertId },
      },
    } = this.props;

    await store.alertGroupStore.unpageUser(alertId, userId);

    this.update();
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

    const integration = store.alertReceiveChannelStore.getIntegration(incident.alert_receive_channel);

    const showLinkTo = !incident.dependent_alert_groups.length && !incident.root_alert_group && !incident.resolved;

    const integrationNameWithEmojies = <Emoji text={incident.alert_receive_channel.verbal_name} />;

    return (
      <Block className={cx('block')}>
        <VerticalGroup>
          <HorizontalGroup justify="space-between">
            <HorizontalGroup className={cx('title')}>
              <PluginLink query={{ page: 'alert-groups', ...query }}>
                <IconButton name="arrow-left" size="xl" />
              </PluginLink>
              {/* @ts-ignore*/}
              <HorizontalGroup align="baseline">
                <Text.Title level={3} data-testid="incident-title">
                  #{incident.inside_organization_number} {incident.render_for_web.title}
                </Text.Title>
                {incident.root_alert_group && (
                  <Text type="secondary">
                    Attached to{' '}
                    <PluginLink query={{ page: 'alert-groups', id: incident.root_alert_group.pk }}>
                      #{incident.root_alert_group.inside_organization_number}{' '}
                      {incident.root_alert_group.render_for_web.title}
                    </PluginLink>{' '}
                    <WithPermissionControlTooltip userAction={UserActions.AlertGroupsWrite}>
                      <Button
                        variant="secondary"
                        onClick={() => this.getUnattachClickHandler(incident.pk)}
                        size="sm"
                        disabled={incident.is_restricted}
                      >
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
                    disabled={incident.is_restricted}
                  />
                )}
                <a href={incident.slack_permalink} target="_blank" rel="noreferrer">
                  <IconButton
                    name="slack"
                    tooltip="View in Slack"
                    className={cx('title-icon')}
                    disabled={incident.is_restricted}
                  />
                </a>
                <CopyToClipboard
                  text={window.location.href}
                  onCopy={() => {
                    openNotification('Link copied');
                  }}
                >
                  <IconButton
                    name="copy"
                    tooltip="Copy link"
                    className={cx('title-icon')}
                    disabled={incident.is_restricted}
                  />
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
                  onSilence={this.getSilenceClickHandler(incident)}
                  onUnsilence={this.getUnsilenceClickHandler(incident)}
                />
              </div>

              {integration && (
                <HorizontalGroup>
                  <PluginLink
                    disabled={incident.alert_receive_channel.deleted}
                    query={{ page: 'integrations', id: incident.alert_receive_channel.id }}
                  >
                    <Button
                      disabled={incident.alert_receive_channel.deleted || incident.is_restricted}
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

                  <Tooltip
                    placement="top"
                    content={
                      incident.render_for_web.source_link === null
                        ? `The integration template Source Link is empty`
                        : 'Go to source'
                    }
                  >
                    <a href={incident.render_for_web.source_link} target="_blank" rel="noreferrer">
                      <Button
                        variant="secondary"
                        fill="outline"
                        size="sm"
                        disabled={incident.render_for_web.source_link === null || incident.is_restricted}
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
              {getActionButtons(incident, cx, {
                onResolve: this.getOnActionButtonClick(incident.pk, AlertAction.Resolve),
                onUnacknowledge: this.getOnActionButtonClick(incident.pk, AlertAction.unAcknowledge),
                onUnresolve: this.getOnActionButtonClick(incident.pk, AlertAction.unResolve),
                onAcknowledge: this.getOnActionButtonClick(incident.pk, AlertAction.Acknowledge),
                onSilence: this.getSilenceClickHandler(incident),
                onUnsilence: this.getUnsilenceClickHandler(incident),
              })}
              <PluginBridge plugin={SupportedPlugin.Incident}>
                <a href={incident.declare_incident_link} target="_blank" rel="noreferrer">
                  <Button variant="secondary" size="md" icon="fire" disabled={incident.is_restricted}>
                    Declare incident
                  </Button>
                </a>
              </PluginBridge>
            </HorizontalGroup>

            <HorizontalGroup>
              <EscalationVariants
                variant="secondary"
                hideSelected
                value={prepareForEdit(incident.paged_users)}
                disabled={incident.is_restricted}
                onUpdateEscalationVariants={this.handleAddResponders}
              />

              <Button
                disabled={incident.alert_receive_channel.deleted || incident.is_restricted}
                variant="secondary"
                icon="edit"
                onClick={this.showIntegrationSettings}
              >
                Edit templates
              </Button>
            </HorizontalGroup>
          </HorizontalGroup>
        </VerticalGroup>
      </Block>
    );
  };

  handleAddResponders = async (data) => {
    const {
      store,
      match: {
        params: { id: alertId },
      },
    } = this.props;

    await store.directPagingStore.updateAlertGroup(
      alertId,
      prepareForUpdate(data.userResponders, data.scheduleResponders)
    );

    this.update();
  };

  showIntegrationSettings = () => {
    this.setState({ showIntegrationSettings: true });
  };

  showAttachIncidentForm = () => {
    this.setState({ showAttachIncidentForm: true });
  };

  getUnattachClickHandler = (pk: Alert['pk']) => {
    const { store } = this.props;

    return store.alertGroupStore.unattachAlert(pk).then(this.update);
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
      <div>
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
                      {item.author && item.author.username} via {ResolutionNoteSourceTypesToDisplayName[item.type]}
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
            disabled={incident.is_restricted}
            onChange={(e: any) => this.setState({ resolutionNoteText: e.target.value })}
          />
        </Field>
        <WithPermissionControlTooltip userAction={UserActions.AlertGroupsWrite}>
          <ToolbarButton
            icon="plus"
            variant="primary"
            onClick={this.handleCreateResolutionNote}
            disabled={isResolutionNoteTextEmpty || incident.is_restricted}
          >
            Add resolution note
          </ToolbarButton>
        </WithPermissionControlTooltip>
      </div>
    );
  };

  filterTimeline = (timeline: TimeLineItem[]) => {
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

  handleCreateResolutionNote = () => {
    const {
      store,
      match: {
        params: { id },
      },
    } = this.props;

    const { resolutionNoteText } = this.state;
    store.resolutionNotesStore
      .createResolutionNote(id, resolutionNoteText)
      .then(() => {
        this.setState({ resolutionNoteText: '' });
      })
      .then(this.update);
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

  getOnActionButtonClick = (incidentId: string, action: AlertAction) => {
    const { store } = this.props;

    return (e: SyntheticEvent) => {
      e.stopPropagation();

      return store.alertGroupStore.doIncidentAction(incidentId, action, false);
    };
  };

  getSilenceClickHandler = (alert: AlertType) => {
    const { store } = this.props;

    return (value: number) => {
      return store.alertGroupStore.doIncidentAction(alert.pk, AlertAction.Silence, false, {
        delay: value,
      });
    };
  };

  getUnsilenceClickHandler = (alert: AlertType) => {
    const { store } = this.props;

    return (event: any) => {
      event.stopPropagation();

      return store.alertGroupStore.doIncidentAction(alert.pk, AlertAction.unSilence, false);
    };
  };

  getIncidentDatetimeReference = (incident: Alert | GroupedAlert): string => {
    let datetimeReference;
    if ((incident as Alert).last_alert_at || incident.created_at) {
      const m = moment((incident as Alert).last_alert_at || incident.created_at);
      datetimeReference = `(${m.fromNow()}, ${m.toString()})`;
    }

    return datetimeReference;
  };
}

function Incident({ incident }: { incident: Alert; datetimeReference: string }) {
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
  disabled,
}: {
  id: string;
  disabled: boolean;
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
        <GroupedIncident
          key={alert.id}
          incident={alert}
          disabled={disabled}
          datetimeReference={getIncidentDatetimeReference(alert)}
        />
      ))}
    </Collapse>
  );
}

function GroupedIncident({
  incident,
  datetimeReference,
  disabled,
}: {
  incident: GroupedAlert;
  datetimeReference: string;
  disabled: boolean;
}) {
  const store = useStore();
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
                <IconButton name="arrow" onClick={() => openIncidentResponse(incident)} disabled={disabled} />
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
    const currentIncidentRawResponse = await store.alertGroupStore.getPayloadForIncident(incident.id);
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
              <Button
                size="sm"
                onClick={() => getUnattachClickHandler(incident.pk)}
                variant="secondary"
                disabled={incident.is_restricted}
              >
                Unattach
              </Button>
            </WithPermissionControlTooltip>
          </HorizontalGroup>
        );
      })}
    </Collapse>
  );
}

export default withRouter(withMobXProviderContext(IncidentPage));
