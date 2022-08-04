import React, { SyntheticEvent } from 'react';

import { AppRootProps } from '@grafana/data';
import { getLocationSrv } from '@grafana/runtime';
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
} from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import moment from 'moment';
import CopyToClipboard from 'react-copy-to-clipboard';
import Emoji from 'react-emoji-render';
import reactStringReplace from 'react-string-replace';

import Collapse from 'components/Collapse/Collapse';
import Block from 'components/GBlock/Block';
import IntegrationLogo from 'components/IntegrationLogo/IntegrationLogo';
import WrongTeamStub from 'components/NotFoundInTeam/WrongTeamStub';
import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import AttachIncidentForm from 'containers/AttachIncidentForm/AttachIncidentForm';
import IntegrationSettings from 'containers/IntegrationSettings/IntegrationSettings';
import { IntegrationSettingsTab } from 'containers/IntegrationSettings/IntegrationSettings.types';
import { WithPermissionControl } from 'containers/WithPermissionControl/WithPermissionControl';
import {
  Alert as AlertType,
  Alert,
  AlertAction,
  TimeLineItem,
  TimeLineRealm,
} from 'models/alertgroup/alertgroup.types';
import { ResolutionNoteSourceTypesToDisplayName } from 'models/resolution_note/resolution_note.types';
import { WithStoreProps } from 'state/types';
import { UserAction } from 'state/userAction';
import { withMobXProviderContext } from 'state/withStore';
import { openNotification } from 'utils';
import sanitize from 'utils/sanitize';

import { getActionButtons, getIncidentStatusTag, renderRelatedUsers } from './Incident.helpers';

import styles from './Incident.module.css';

const cx = cn.bind(styles);

interface IncidentPageProps extends WithStoreProps, AppRootProps {}

interface IncidentPageState {
  showIntegrationSettings?: boolean;
  showAttachIncidentForm?: boolean;
  notFound?: boolean;
  wrongTeamError?: boolean;
  wrongTeamNoPermissions?: boolean;
  teamToSwitch?: { name: string; id: string };
  timelineFilter: string;
  resolutionNoteText: string;
}

@observer
class IncidentPage extends React.Component<IncidentPageProps, IncidentPageState> {
  state: IncidentPageState = {
    timelineFilter: 'all',
    resolutionNoteText: '',
    wrongTeamError: false,
    wrongTeamNoPermissions: false,
  };

  componentDidMount() {
    const { store } = this.props;

    this.update();

    store.alertGroupStore.updateSilenceOptions();
  }

  componentDidUpdate(prevProps: IncidentPageProps) {
    if (this.props.query.id !== prevProps.query.id) {
      this.update();
    }
  }

  update = () => {
    const {
      store,
      query: { id },
    } = this.props;

    store.alertGroupStore.getAlert(id).catch((error) => {
      if (error.response) {
        if (error.response.status === 404) {
          this.setState({ notFound: true });
        } else if (error.response.status === 403 && error.response.data.error_code === 'wrong_team') {
          let res = error.response.data;
          if (res.owner_team) {
            this.setState({ wrongTeamError: true, teamToSwitch: { name: res.owner_team.name, id: res.owner_team.id } });
          } else {
            this.setState({ wrongTeamError: true, wrongTeamNoPermissions: true });
          }
          return;
        }
      }

      this.setState({ notFound: true });
    });
  };

  render() {
    const {
      store,
      query: { id, cursor, start, perpage },
    } = this.props;

    const {
      showIntegrationSettings,
      showAttachIncidentForm,
      notFound,
      wrongTeamError,
      teamToSwitch,
      wrongTeamNoPermissions,
    } = this.state;

    const { alertReceiveChannelStore } = store;

    const { isMobile } = store;

    const { alerts } = store.alertGroupStore;

    const incident = alerts.get(id);
    const currentTeamId = store.userStore.currentUser?.current_team;
    const currentTeamName = store.grafanaTeamStore.items[currentTeamId]?.name;
    if (notFound) {
      return (
        <div className={cx('root')}>
          <div className={cx('not-found')}>
            <VerticalGroup spacing="lg" align="center">
              <Text.Title level={1}>404</Text.Title>
              <Text.Title level={4}>Incident not found</Text.Title>
              <PluginLink query={{ page: 'incidents', cursor, start, perpage }}>
                <Button variant="secondary" icon="arrow-left" size="md">
                  Go to incidents page
                </Button>
              </PluginLink>
            </VerticalGroup>
          </div>
        </div>
      );
    }

    if (wrongTeamError) {
      return (
        <WrongTeamStub
          objectName="alert group"
          pageName="incidents"
          currentTeam={currentTeamName}
          switchToTeam={teamToSwitch}
          wrongTeamNoPermissions={wrongTeamNoPermissions}
        />
      );
    }

    if (!incident) {
      return (
        <div className={cx('root')}>
          <LoadingPlaceholder text="Loading alert group..." />
        </div>
      );
    }

    const integration = store.alertReceiveChannelStore.getIntegration(incident.alert_receive_channel);

    return (
      <>
        <div className={cx('root')}>
          {this.renderHeader()}
          <div className={cx('content')}>
            <div className={cx('column')}>
              {this.renderIncident(incident)}
              {this.renderGroupedIncidents()}
              {this.renderAttachedIncidents()}
            </div>
            <div className={cx('column')}>{this.renderTimeline()}</div>
          </div>
        </div>
        {showIntegrationSettings && (
          <IntegrationSettings
            alertGroupId={incident.pk}
            onUpdate={() => {
              alertReceiveChannelStore.updateItem(incident.alert_receive_channel.id);
            }}
            onUpdateTemplates={() => {
              store.alertGroupStore.getAlert(id);
            }}
            startTab={IntegrationSettingsTab.Templates}
            id={incident.alert_receive_channel.id}
            onHide={() =>
              this.setState({
                showIntegrationSettings: undefined,
              })
            }
          />
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
    );
  }

  renderHeader = () => {
    const {
      store,
      query: { id, cursor, start, perpage },
    } = this.props;

    const { alerts } = store.alertGroupStore;

    const incident = alerts.get(id);

    const integration = store.alertReceiveChannelStore.getIntegration(incident.alert_receive_channel);

    const showLinkTo = !incident.dependent_alert_groups.length && !incident.root_alert_group && !incident.resolved;

    return (
      <Block withBackground>
        <VerticalGroup>
          <HorizontalGroup className={cx('title')}>
            <PluginLink query={{ page: 'incidents', cursor, start, perpage }}>
              <IconButton name="arrow-left" size="xxl" />
            </PluginLink>
            {/* @ts-ignore*/}
            <HorizontalGroup align="baseline">
              <Text.Title level={3}>
                {' '}
                / #{incident.inside_organization_number} {incident.render_for_web.title}
              </Text.Title>
              {incident.root_alert_group && (
                <Text type="secondary">
                  Attached to{' '}
                  <PluginLink query={{ page: 'incident', id: incident.root_alert_group.pk }}>
                    #{incident.root_alert_group.inside_organization_number}{' '}
                    {incident.root_alert_group.render_for_web.title}
                  </PluginLink>{' '}
                  <WithPermissionControl userAction={UserAction.UpdateIncidents}>
                    <Button variant="secondary" onClick={this.getUnattachClickHandler(incident.pk)} size="sm">
                      Unattach
                    </Button>
                  </WithPermissionControl>
                </Text>
              )}
            </HorizontalGroup>
          </HorizontalGroup>
          <div className={cx('info-row')}>
            <HorizontalGroup>
              {getIncidentStatusTag(incident)} | <Emoji text={incident.alert_receive_channel.verbal_name} />|
              <IntegrationLogo integration={integration} scale={0.1} />
              {integration && <Text type="secondary"> {integration?.display_name}</Text>}
              {integration && '|'}
              <Text type="secondary">{renderRelatedUsers(incident, true)}</Text>
            </HorizontalGroup>
          </div>
          <HorizontalGroup justify="space-between" className={cx('buttons-row')}>
            <div>
              {getActionButtons(incident, cx, {
                onResolve: this.getOnActionButtonClick(incident.pk, AlertAction.Resolve),
                onUnacknowledge: this.getOnActionButtonClick(incident.pk, AlertAction.unAcknowledge),
                onUnresolve: this.getOnActionButtonClick(incident.pk, AlertAction.unResolve),
                onAcknowledge: this.getOnActionButtonClick(incident.pk, AlertAction.Acknowledge),
                onSilence: this.getSilenceClickHandler(incident),
                onUnsilence: this.getUnsilenceClickHandler(incident),
              })}
            </div>
            <HorizontalGroup>
              <CopyToClipboard
                text={window.location.href}
                onCopy={() => {
                  openNotification('Link copied');
                }}
              >
                <Button variant="primary" size="sm" icon="copy">
                  Copy Link
                </Button>
              </CopyToClipboard>
              <a href={incident.permalink} target="_blank">
                <Button variant="primary" size="sm" icon="slack">
                  View in Slack
                </Button>
              </a>
              {showLinkTo && (
                <Button variant="primary" size="sm" icon="link" onClick={this.showAttachIncidentForm}>
                  Attach to another incident
                </Button>
              )}
              <PluginLink query={{ page: 'integrations', id: incident.alert_receive_channel.id }}>
                <Button disabled={incident.alert_receive_channel.deleted} variant="secondary" size="sm" icon="compass">
                  Go to Integration
                </Button>
              </PluginLink>
              <Button
                disabled={incident.alert_receive_channel.deleted}
                variant="secondary"
                size="sm"
                icon="edit"
                onClick={this.showIntegrationSettings}
              >
                Edit rendering, grouping and other templates
              </Button>
            </HorizontalGroup>
          </HorizontalGroup>
        </VerticalGroup>
      </Block>
    );
  };

  showIntegrationSettings = () => {
    this.setState({ showIntegrationSettings: true });
  };

  showAttachIncidentForm = () => {
    this.setState({ showAttachIncidentForm: true });
  };

  renderIncident = (incident: Alert) => {
    let datetimeReference;

    if (incident.last_alert_at || incident.created_at) {
      const m = moment(incident.last_alert_at || incident.created_at);
      datetimeReference = `(${m.fromNow()}, ${m.toString()})`;
    }

    return (
      <div key={incident.pk} className={cx('incident')}>
        <HorizontalGroup wrap>
          <Text.Title type="secondary" level={4}>
            {incident.inside_organization_number
              ? `#${incident.inside_organization_number} ${incident.render_for_web.title}`
              : incident.render_for_web.title}
          </Text.Title>
          <Text type="secondary">{datetimeReference}</Text>
        </HorizontalGroup>
        <div
          className={cx('message')}
          dangerouslySetInnerHTML={{
            __html: sanitize(incident.render_for_web.message),
          }}
        />
        {incident.render_for_web.image_url && <img className={cx('image')} src={incident.render_for_web.image_url} />}
      </div>
    );
  };

  renderGroupedIncidents() {
    const {
      store,
      query: { id },
    } = this.props;

    const incident = store.alertGroupStore.alerts.get(id);

    const alerts = incident.alerts;
    if (!alerts) {
      return null;
    }

    const latestAlert = alerts[alerts.length - 1];
    const latestAlertMoment = moment(latestAlert.created_at);

    return (
      <Collapse
        headerWithBackground
        className={cx('collapse')}
        isOpen
        label={
          <HorizontalGroup wrap>
            {incident.alerts_count} Grouped Alerts
            <Text type="secondary">
              (latest {latestAlertMoment.fromNow()}, {latestAlertMoment.toString()})
            </Text>
          </HorizontalGroup>
        }
        contentClassName={cx('incidents-content')}
      >
        {alerts.map(this.renderIncident)}
      </Collapse>
    );
  }

  renderAttachedIncidents = () => {
    const {
      store,
      query: { id },
    } = this.props;

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
        label={<HorizontalGroup wrap>{incident.dependent_alert_groups.length} Attached Incidents</HorizontalGroup>}
        contentClassName={cx('incidents-content')}
      >
        {alerts.map((incident) => {
          return (
            <HorizontalGroup key={incident.pk} justify={'space-between'}>
              <PluginLink query={{ page: 'incident', id: incident.pk }}>
                #{incident.inside_organization_number} {incident.render_for_web.title}
              </PluginLink>
              {/* <Emoji text={incident.alert_receive_channel?.verbal_name || ''} />*/}
              <WithPermissionControl userAction={UserAction.UpdateIncidents}>
                <Button size="sm" onClick={this.getUnattachClickHandler(incident.pk)} variant="secondary">
                  Unattach
                </Button>
              </WithPermissionControl>
            </HorizontalGroup>
          );
        })}
      </Collapse>
    );
  };

  getUnattachClickHandler = (pk: Alert['pk']) => {
    const { store } = this.props;

    return () => {
      store.alertGroupStore.unattachAlert(pk).then(this.update);
    };
  };

  renderTimeline = () => {
    const {
      store,
      query: { id },
    } = this.props;

    const incident = store.alertGroupStore.alerts.get(id);

    if (!incident.render_after_resolve_report_json) {
      return null;
    }

    const timeline = this.filterTimeline(incident.render_after_resolve_report_json);
    const { timelineFilter, resolutionNoteText } = this.state;
    const isResolutionNoteTextEmpty = resolutionNoteText === '';
    return (
      <>
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
        <ul className={cx('timeline')}>
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
                    {reactStringReplace(item.action, /\{\{([^}]+)\}\}/g, this.getPlaceholderReplaceFn(item))}
                  </Text>
                  <Text type="secondary" size="small">
                    {moment(item.created_at).format('MMM DD, YYYY hh:mm A')}
                  </Text>
                </VerticalGroup>
              </HorizontalGroup>
            </li>
          ))}
        </ul>
        <Field label="Leave a resolution note" description="Will also show up in the thread of incident in Slack">
          <TextArea
            value={resolutionNoteText}
            onChange={(e: any) => this.setState({ resolutionNoteText: e.target.value })}
          />
        </Field>
        <ToolbarButton
          icon="plus"
          variant="primary"
          onClick={this.handleCreateResolutionNote}
          disabled={isResolutionNoteTextEmpty}
        >
          Add resolution note
        </ToolbarButton>
      </>
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
      query: { id },
    } = this.props;

    const { resolutionNoteText } = this.state;
    store.resolutionNotesStore
      .createResolutionNote(id, resolutionNoteText)
      .then(() => {
        this.setState({ resolutionNoteText: '' });
      })
      .then(this.update);
  };

  getPlaceholderReplaceFn = (entity: any) => {
    return (match: string) => {
      switch (match) {
        case 'author':
          const {
            store: { userStore },
          } = this.props;

          const user = userStore.items?.[entity?.author?.pk];

          return (
            /* <Tooltip placement="top" content={<UserSummary id={entity?.author?.pk} />}>*/
            <span
              onClick={() => {
                getLocationSrv().update({ query: { page: 'users', id: entity?.author?.pk } });
              }}
              style={{ textDecoration: 'underline', cursor: 'pointer' }}
            >
              {entity.author?.username}
            </span>
            /* </Tooltip>*/
          );
        default:
          console.warn('Unknown render_after_resolve_report_json enity placeholder');
          return '';
      }
    };
  };

  getOnActionButtonClick = (incidentId: string, action: AlertAction) => {
    const { store } = this.props;

    return (e: SyntheticEvent) => {
      e.stopPropagation();

      store.alertGroupStore.doIncidentAction(incidentId, action, false);
    };
  };

  getSilenceClickHandler = (alert: AlertType) => {
    const { store } = this.props;

    return (value: number) => {
      store.alertGroupStore.doIncidentAction(alert.pk, AlertAction.Silence, false, {
        delay: value,
      });
    };
  };

  getUnsilenceClickHandler = (alert: AlertType) => {
    const { store } = this.props;

    return (event: any) => {
      event.stopPropagation();

      store.alertGroupStore.doIncidentAction(alert.pk, AlertAction.unSilence, false);
    };
  };
}

export default withMobXProviderContext(IncidentPage);
