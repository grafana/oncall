import React, { useState, SyntheticEvent } from 'react';

import { cx } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { LabelTag } from '@grafana/labels';
import {
  Button,
  Icon,
  IconButton,
  LoadingPlaceholder,
  RadioButtonGroup,
  TextArea,
  ToolbarButton,
  Stack,
  Field,
  Modal,
  Tooltip,
  Divider,
  withTheme2,
  useStyles2,
} from '@grafana/ui';
import { OnCallPluginExtensionPoints } from 'app-types';
import { UserActions } from 'helpers/authorization/authorization';
import { INTEGRATION_SERVICENOW, PLUGIN_ROOT, StackSize } from 'helpers/consts';
import { openNotification } from 'helpers/helpers';
import { PropsWithRouter, withRouter } from 'helpers/hoc';
import { sanitize } from 'helpers/sanitize';
import { parseURL } from 'helpers/url';
import Linkify from 'linkify-react';
import { observer } from 'mobx-react';
import moment from 'moment-timezone';
import CopyToClipboard from 'react-copy-to-clipboard';
import Emoji from 'react-emoji-render';
import reactStringReplace from 'react-string-replace';

import { Collapse } from 'components/Collapse/Collapse';
import { ExtensionLinkDropdown } from 'components/ExtensionLinkMenu/ExtensionLinkDropdown';
import { FullPageError } from 'components/FullPageError/FullPageError';
import { Block } from 'components/GBlock/Block';
import { IntegrationLogo } from 'components/IntegrationLogo/IntegrationLogo';
import { PageErrorHandlingWrapper, PageBaseState } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper';
import {
  getWrongTeamResponseInfo,
  initErrorDataState,
} from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper.helpers';
import { PluginLink } from 'components/PluginLink/PluginLink';
import { CUSTOM_SILENCE_VALUE } from 'components/Policy/Policy.consts';
import { RenderConditionally } from 'components/RenderConditionally/RenderConditionally';
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
import { IncidentSilenceModal } from 'pages/incidents/parts/IncidentSilenceModal';
import { AppFeature } from 'state/features';
import { PageProps, WithStoreProps } from 'state/types';
import { useStore } from 'state/useStore';
import { withMobXProviderContext } from 'state/withStore';

import { getActionButtons } from './Incident.helpers';
import { getIncidentStyles } from './Incident.styles';

const INTEGRATION_NAME_LENGTH_LIMIT = 30;

interface RouteProps {
  id: string;
}

interface IncidentPageProps extends WithStoreProps, PageProps, PropsWithRouter<RouteProps> {
  theme: GrafanaTheme2;
}

interface IncidentPageState extends PageBaseState {
  showIntegrationSettings?: boolean;
  showAttachIncidentForm?: boolean;
  timelineFilter: string;
  resolutionNoteText: string;
  silenceModalData: { incident: ApiSchemas['AlertGroup'] };
}

@observer
class _IncidentPage extends React.Component<IncidentPageProps, IncidentPageState> {
  state: IncidentPageState = {
    timelineFilter: 'all',
    resolutionNoteText: '',
    errorData: initErrorDataState(),
    silenceModalData: undefined,
  };

  componentDidMount() {
    this.update();
  }

  componentWillUnmount(): void {
    this.props.store.setPageTitle('');
  }

  componentDidUpdate(prevProps: IncidentPageProps) {
    if (this.props.router.params.id !== prevProps.router.params.id) {
      this.update();
    }
  }

  update = async () => {
    this.setState({ errorData: initErrorDataState() }); // reset wrong team error to false

    const {
      store,
      router: {
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
      router: {
        params: { id },
      },
    } = this.props;

    const { errorData, showIntegrationSettings, showAttachIncidentForm, silenceModalData } = this.state;
    const { isNotFoundError, isWrongTeamError, isUnknownError } = errorData;
    const { alerts } = store.alertGroupStore;
    const styles = getIncidentStyles(this.props.theme);

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
              onSilence: this.getSilenceClickHandler(incident),
              onUnsilence: this.getUnsilenceClickHandler(id),
            },
            true
          )}
        />
      );
    }

    if (!incident && !isNotFoundError && !isWrongTeamError) {
      return (
        <div>
          <LoadingPlaceholder text="Loading Alert Group..." />
        </div>
      );
    }

    return (
      <PageErrorHandlingWrapper errorData={errorData} objectName="alert group" pageName="incidents">
        {() => (
          <div>
            {errorData.isNotFoundError ? (
              <div className={styles.notFound}>
                <Stack direction="column" gap={StackSize.lg} alignItems="center">
                  <Text.Title level={1}>404</Text.Title>
                  <Text.Title level={4}>Alert group not found</Text.Title>
                  <PluginLink query={{ page: 'alert-groups', cursor, start, perpage }}>
                    <Button variant="secondary" icon="arrow-left" size="md">
                      Go to Alert Groups page
                    </Button>
                  </PluginLink>
                </Stack>
              </div>
            ) : (
              <>
                {this.renderHeader()}
                <div className={styles.content}>
                  <div className={styles.column}>
                    <Incident incident={incident} datetimeReference={this.getIncidentDatetimeReference(incident)} />
                    <GroupedIncidentsList
                      id={incident.pk}
                      getIncidentDatetimeReference={this.getIncidentDatetimeReference}
                    />
                    <AttachedIncidentsList id={incident.pk} getUnattachClickHandler={this.getUnattachClickHandler} />
                  </div>
                  <div className={styles.column}>
                    <Stack direction="column">
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
                    </Stack>
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

            {/* Modal where users can input their custom duration for silencing an alert group */}
            <RenderConditionally
              shouldRender={Boolean(silenceModalData?.incident)}
              render={() => (
                <IncidentSilenceModal
                  alertGroupID={silenceModalData.incident.inside_organization_number}
                  alertGroupName={silenceModalData.incident.render_for_web?.title}
                  isOpen
                  onDismiss={() => this.setState({ silenceModalData: undefined })}
                  onSave={(duration: number) => {
                    this.setState({ silenceModalData: undefined });
                    store.alertGroupStore.doIncidentAction(silenceModalData.incident.pk, AlertAction.Silence, duration);
                  }}
                />
              )}
            />
          </div>
        )}
      </PageErrorHandlingWrapper>
    );
  }

  handlePagedUserRemove = (userId: ApiSchemas['User']['pk']) => {
    return async () => {
      const {
        router: {
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
      router: {
        params: { id },
      },
    } = this.props;

    const { alerts } = store.alertGroupStore;
    const styles = getIncidentStyles(this.props.theme);

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
      <Block className={styles.block}>
        <Stack direction="column">
          <Stack justifyContent="space-between">
            <Stack>
              <PluginLink query={{ page: 'alert-groups', ...query }}>
                <IconButton aria-label="Go Back" name="arrow-left" size="xl" />
              </PluginLink>
              {/* @ts-ignore*/}
              <Stack align="baseline">
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
              </Stack>
            </Stack>
            <Stack alignItems="center">
              <Text>
                {showLinkTo && (
                  <IconButton
                    name="code-branch"
                    onClick={this.showAttachIncidentForm}
                    tooltip="Attach to another Alert Group"
                    className={styles.titleIcon}
                  />
                )}
                <a href={incident.slack_permalink} target="_blank" rel="noreferrer">
                  <IconButton name="slack" tooltip="View in Slack" className={styles.titleIcon} />
                </a>
                <CopyToClipboard
                  text={window.location.href}
                  onCopy={() => {
                    openNotification('Link copied');
                  }}
                >
                  <IconButton name="copy" tooltip="Copy link" className={styles.titleIcon} />
                </CopyToClipboard>
              </Text>
            </Stack>
          </Stack>
          <div className={styles.infoRow}>
            <Stack>
              <div className={styles.statusTagContainer}>
                <IncidentDropdown
                  alert={incident}
                  onResolve={this.getOnActionButtonClick(incident.pk, AlertAction.Resolve)}
                  onUnacknowledge={this.getOnActionButtonClick(incident.pk, AlertAction.unAcknowledge)}
                  onUnresolve={this.getOnActionButtonClick(incident.pk, AlertAction.unResolve)}
                  onAcknowledge={this.getOnActionButtonClick(incident.pk, AlertAction.Acknowledge)}
                  onSilence={this.getSilenceClickHandler(incident)}
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
                    <Stack direction="column" gap={StackSize.sm}>
                      {incident.labels.map((label) => (
                        <LabelTag label={label.key.name} value={label.value.name} key={label.key.id} />
                      ))}
                    </Stack>
                  }
                />
              )}

              {integration && (
                <Stack>
                  <PluginLink
                    disabled={incident.alert_receive_channel.deleted}
                    query={{ page: 'integrations', id: incident.alert_receive_channel.id }}
                  >
                    <Button
                      disabled={incident.alert_receive_channel.deleted}
                      variant="secondary"
                      fill="outline"
                      size="sm"
                      className={styles.labelButton}
                    >
                      <Tooltip
                        placement="top"
                        content={
                          incident.alert_receive_channel.verbal_name.length > INTEGRATION_NAME_LENGTH_LIMIT
                            ? integrationNameWithEmojies
                            : 'Go to Integration'
                        }
                      >
                        <div className={cx(styles.labelButtonText, styles.sourceName)}>
                          <div className={styles.integrationLogo}>
                            <IntegrationLogo integration={integration} scale={0.08} />
                          </div>
                          <div className={styles.labelButtonText}>{integrationNameWithEmojies}</div>
                        </div>
                      </Tooltip>
                    </Button>
                  </PluginLink>

                  {isServiceNow && (
                    <Button variant="secondary" fill="outline" size="sm" className={styles.labelButton}>
                      <Stack gap={StackSize.xs}>
                        <Icon name="exchange-alt" />
                        <span>Service Now</span>
                      </Stack>
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
                        className={styles.labelButton}
                        icon="external-link-alt"
                      >
                        Source
                      </Button>
                    </a>
                  </Tooltip>
                </Stack>
              )}
            </Stack>
          </div>
          {/* TODO: Check if previous styles were being applied */}
          <Stack justifyContent="space-between">
            <Stack>
              {getActionButtons(incident, {
                onResolve: this.getOnActionButtonClick(incident.pk, AlertAction.Resolve),
                onUnacknowledge: this.getOnActionButtonClick(incident.pk, AlertAction.unAcknowledge),
                onUnresolve: this.getOnActionButtonClick(incident.pk, AlertAction.unResolve),
                onAcknowledge: this.getOnActionButtonClick(incident.pk, AlertAction.Acknowledge),
                onSilence: this.getSilenceClickHandler(incident),
                onUnsilence: this.getUnsilenceClickHandler(incident.pk),
              })}
              <ExtensionLinkDropdown
                alertGroup={incident}
                extensionPointId={OnCallPluginExtensionPoints.AlertGroupAction}
                declareIncidentLink={incident.declare_incident_link}
                grafanaIncidentId={incident.grafana_incident_id}
              />
            </Stack>

            <Button
              disabled={incident.alert_receive_channel.deleted}
              variant="secondary"
              icon="edit"
              onClick={this.showIntegrationSettings}
            >
              Edit templates
            </Button>
          </Stack>
        </Stack>
      </Block>
    );
  };

  handleAddUserResponder = async (user: Omit<UserResponder, 'type'>) => {
    const {
      store,
      router: {
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
      router: {
        params: { id },
      },
      theme,
    } = this.props;

    const styles = getIncidentStyles(theme);
    const incident = store.alertGroupStore.alerts.get(id);

    if (!incident.render_after_resolve_report_json) {
      return null;
    }

    const timeline = this.filterTimeline(incident.render_after_resolve_report_json);
    const { timelineFilter, resolutionNoteText } = this.state;
    const isResolutionNoteTextEmpty = resolutionNoteText === '';
    return (
      <Block bordered>
        <Text.Title type="primary" level={4} className={styles.timelineTitle}>
          Timeline
        </Text.Title>
        <RadioButtonGroup
          className={styles.timelineFilter}
          options={[
            { label: 'Show full timeline', value: 'all' },
            { label: 'Resolution notes only', value: TimeLineRealm.ResolutionNote },
          ]}
          value={timelineFilter}
          onChange={(value) => {
            this.setState({ timelineFilter: value });
          }}
        />
        <ul className={styles.timeline} data-testid="incident-timeline-list">
          {timeline.map((item: TimeLineItem, idx: number) => (
            <li key={idx} className={styles.timelineItem}>
              <Stack alignItems="flex-start">
                <div
                  className={cx(styles.timelineIconBackground, {
                    blue: item.realm === TimeLineRealm.ResolutionNote,
                  })}
                >
                  {this.renderTimelineItemIcon(item.realm)}
                </div>
                <Stack direction="column" gap={StackSize.none}>
                  {item.realm === TimeLineRealm.ResolutionNote && (
                    <Text type="secondary" size="small">
                      {item.author && item.author.username} via{' '}
                      {ResolutionNoteSourceTypesToDisplayName[item.type] || 'Web'}
                    </Text>
                  )}
                  <Text type="primary">
                    <Linkify
                      options={{
                        render: ({ attributes, content }) => (
                          <a {...attributes} rel="noreferrer noopener" target="_blank">
                            <Text underline>{content}</Text>
                          </a>
                        ),
                      }}
                    >
                      {this.replaceTextInResolutionNote(item)}
                    </Linkify>
                  </Text>
                  <Text type="secondary" size="small">
                    {moment(item.created_at).format('MMM DD, YYYY HH:mm:ss Z')}
                  </Text>
                </Stack>
              </Stack>
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
      router: {
        params: { id },
      },
    } = this.props;

    const { resolutionNoteText } = this.state;

    await store.resolutionNotesStore.createResolutionNote(id, resolutionNoteText);
    this.setState({ resolutionNoteText: '' });
    await this.update();
  };

  getPlaceholderReplaceFn = (entity: TimeLineItem) => {
    // eslint-disable-next-line react/display-name
    return (match: string) => {
      switch (match) {
        case 'author':
          return (
            <a href={`${PLUGIN_ROOT}/users/${entity?.author?.pk}`} target="_blank" rel="noopener noreferrer">
              <Text underline>{entity.author?.username}</Text>
            </a>
          );
        case 'escalation_chain':
          return (
            <a href={`${PLUGIN_ROOT}/escalations/${entity.escalation_chain?.pk}`} target="_blank" rel="noopener noreferrer">
              <Text underline>{entity.escalation_chain?.title}</Text>
            </a>
          );
        case 'related_incident':
          return (
            <a href={entity.incident?.incident_link} target="_blank" rel="noopener noreferrer">
              <Text underline>{entity.incident?.incident_title}</Text>
            </a>
          );
        case 'schedule':
          return (
            <a href={`${PLUGIN_ROOT}/schedules/${entity.schedule?.pk}`} target="_blank" rel="noopener noreferrer">
              <Text underline>{entity.schedule?.title}</Text>
            </a>
          );
        case 'webhook':
          return (
            <a href={`${PLUGIN_ROOT}/outgoing_webhooks/${entity.webhook?.pk}`} target="_blank" rel="noopener noreferrer">
              <Text underline>{entity.webhook?.title}</Text>
            </a>
          );
        default:
          return '{{' + match + '}}';
      }
    };
  };

  replaceTextInResolutionNote = (item: TimeLineItem) =>
    reactStringReplace(item.action, /\{\{([^}]+)\}\}/g, this.getPlaceholderReplaceFn(item));

  getOnActionButtonClick = (incidentId: ApiSchemas['AlertGroup']['pk'], action: AlertAction) => {
    const { store } = this.props;

    return (e: SyntheticEvent) => {
      e.stopPropagation();

      return store.alertGroupStore.doIncidentAction(incidentId, action);
    };
  };

  getSilenceClickHandler = (incident: ApiSchemas['AlertGroup']) => {
    const { store } = this.props;

    return (value: number): Promise<void> => {
      if (value === CUSTOM_SILENCE_VALUE) {
        this.setState({ silenceModalData: { incident } });
        return Promise.resolve(); // awaited by other component
      }
      return store.alertGroupStore.doIncidentAction(incident.pk, AlertAction.Silence, value);
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
  const styles = useStyles2(getIncidentStyles);

  return (
    <div key={incident.pk}>
      <div
        className={styles.message}
        dangerouslySetInnerHTML={{
          __html: sanitize(incident.render_for_web.message),
        }}
        data-testid="incident-message"
      />
      {incident.render_for_web.image_url && <img className={styles.image} src={incident.render_for_web.image_url} />}
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
  const styles = useStyles2(getIncidentStyles);

  const alerts = incident.alerts;
  if (!alerts) {
    return null;
  }

  const latestAlert = alerts[0];
  const latestAlertMoment = moment(latestAlert.created_at);

  return (
    <Collapse
      headerWithBackground
      className={styles.collapse}
      isOpen={false}
      label={
        <Stack wrap="wrap">
          <Text>{incident.alerts_count} Grouped Alerts</Text>
          <Text type="secondary">latest {latestAlertMoment.fromNow()},</Text>
          <Text type="secondary">{latestAlertMoment.format('MMM DD, YYYY HH:mm:ss Z').toString()}</Text>
        </Stack>
      }
      contentClassName={styles.incidentsContent}
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
  const styles = useStyles2(getIncidentStyles);

  return (
    <>
      {isModalOpen && (
        <Modal onDismiss={() => setIsModalOpen(false)} closeOnEscape isOpen={isModalOpen} title="Alert Payload">
          <div className={styles.payloadSubtitle}>
            <Stack>
              <Text type="secondary">
                {incident.render_for_web.title} - {datetimeReference}
              </Text>
            </Stack>
          </div>
          <Stack direction="column">
            <SourceCode showCopyToClipboard={false}>{payloadJSON}</SourceCode>
            <Stack justifyContent={'flex-end'}>
              <CopyToClipboard
                text={payloadJSON}
                onCopy={() => {
                  openNotification('Copied!');
                }}
              >
                <Button variant="primary" icon="copy">
                  Copy to Clipboard
                </Button>
              </CopyToClipboard>
            </Stack>
          </Stack>
        </Modal>
      )}

      <div key={incident.id}>
        <div className={styles.incidentRow}>
          <div className={styles.incidentRowLeftSide}>
            <Stack wrap="wrap" justifyContent={'flex-start'}>
              <Text.Title type="secondary" level={4}>
                {incident.render_for_web.title}
              </Text.Title>
              <Text type="secondary">{datetimeReference}</Text>
            </Stack>
          </div>
          <div>
            <Stack justifyContent={'flex-end'}>
              <Tooltip placement="top" content="Alert Payload">
                <IconButton aria-label="Alert Payload" name="arrow" onClick={() => openIncidentResponse(incident)} />
              </Tooltip>
            </Stack>
          </div>
        </div>
        <Text type="secondary">
          <div
            className={styles.message}
            dangerouslySetInnerHTML={{
              __html: sanitize(incident.render_for_web.message),
            }}
          />
        </Text>
        {incident.render_for_web.image_url && <img className={styles.image} src={incident.render_for_web.image_url} />}
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
  const styles = useStyles2(getIncidentStyles);
  const incident = store.alertGroupStore.alerts.get(id);

  if (!incident.dependent_alert_groups.length) {
    return null;
  }

  const alerts = incident.dependent_alert_groups;

  return (
    <Collapse
      headerWithBackground
      className={styles.collapse}
      isOpen
      label={<Stack wrap="wrap">{incident.dependent_alert_groups.length} Attached Alert Groups</Stack>}
      contentClassName={styles.incidentsContent}
    >
      {alerts.map((incident) => {
        return (
          <Stack key={incident.pk} justifyContent={'space-between'}>
            <PluginLink query={{ page: 'alert-groups', id: incident.pk }}>
              #{incident.inside_organization_number} {incident.render_for_web.title}
            </PluginLink>
            <WithPermissionControlTooltip userAction={UserActions.AlertGroupsWrite}>
              <Button size="sm" onClick={() => getUnattachClickHandler(incident.pk)} variant="secondary">
                Unattach
              </Button>
            </WithPermissionControlTooltip>
          </Stack>
        );
      })}
    </Collapse>
  );
}

const AlertGroupStub = ({ buttons }: { buttons: React.ReactNode }) => {
  const styles = useStyles2(getIncidentStyles);
  return (
    <FullPageError
      subtitle="OnCall is not able to receive any information about the current Alert Group. It's unknown if it's firing,
          acknowledged, silenced, or resolved."
    >
      <>
        <div className={styles.alertGroupStubDivider}>
          <Divider />
        </div>
        <Text type="secondary">Meanwhile, you could try changing the status of this Alert Group:</Text>
        <Stack wrap="wrap" justifyContent="center">
          {buttons}
        </Stack>
      </>
    </FullPageError>
  );
};

export const IncidentPage = withRouter<RouteProps, Omit<IncidentPageProps, 'store' | 'meta' | 'theme'>>(
  withMobXProviderContext(withTheme2(_IncidentPage))
);
