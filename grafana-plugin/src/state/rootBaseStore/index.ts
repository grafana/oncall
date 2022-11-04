import { OrgRole } from '@grafana/data';
import { contextSrv } from 'grafana/app/core/core';
import { action, observable } from 'mobx';
import moment from 'moment-timezone';
import qs from 'query-string';
import { OnCallAppPluginMeta } from 'types';

import { AlertReceiveChannelStore } from 'models/alert_receive_channel/alert_receive_channel';
import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { AlertReceiveChannelFiltersStore } from 'models/alert_receive_channel_filters/alert_receive_channel_filters';
import { AlertGroupStore } from 'models/alertgroup/alertgroup';
import { ApiTokenStore } from 'models/api_token/api_token';
import { CloudStore } from 'models/cloud/cloud';
import { EscalationChainStore } from 'models/escalation_chain/escalation_chain';
import { EscalationPolicyStore } from 'models/escalation_policy/escalation_policy';
import { GlobalSettingStore } from 'models/global_setting/global_setting';
import { GrafanaTeamStore } from 'models/grafana_team/grafana_team';
import { HeartbeatStore } from 'models/heartbeat/heartbeat';
import { MaintenanceStore } from 'models/maintenance/maintenance';
import { MatrixStore } from 'models/matrix/matrix';
import { OrganizationLogStore } from 'models/organization_log/organization_log';
import { OutgoingWebhookStore } from 'models/outgoing_webhook/outgoing_webhook';
import { ResolutionNotesStore } from 'models/resolution_note/resolution_note';
import { ScheduleStore } from 'models/schedule/schedule';
import { SlackStore } from 'models/slack/slack';
import { SlackChannelStore } from 'models/slack_channel/slack_channel';
import { TeamStore } from 'models/team/team';
import { TelegramChannelStore } from 'models/telegram_channel/telegram_channel';
import { Timezone } from 'models/timezone/timezone.types';
import { UserStore } from 'models/user/user';
import { UserGroupStore } from 'models/user_group/user_group';
import { makeRequest } from 'network';
import { NavMenuItem } from 'pages/routes';
import { AppFeature } from 'state/features';
import PluginState from 'state/plugin';
import { UserAction } from 'state/userAction';

// ------ Dashboard ------ //

export class RootBaseStore {
  @observable
  appLoading = true;

  @observable
  currentTimezone: Timezone = moment.tz.guess() as Timezone;

  @observable
  backendVersion = '';

  @observable
  backendLicense = '';

  @observable
  initializationError = null;

  @observable
  isMobile = false;

  initialQuery = qs.parse(window.location.search);

  @observable
  selectedAlertReceiveChannel?: AlertReceiveChannel['id'];

  @observable
  isLess1280: boolean;

  @observable
  features?: { [key: string]: boolean };

  @observable
  incidentFilters: any;

  @observable
  incidentsPage: any = this.initialQuery.p ? Number(this.initialQuery.p) : 1;

  @observable
  onCallApiUrl: string;

  @observable
  navMenuItem: NavMenuItem;

  // --------------------------

  userStore: UserStore = new UserStore(this);
  cloudStore: CloudStore = new CloudStore(this);
  grafanaTeamStore: GrafanaTeamStore = new GrafanaTeamStore(this);
  alertReceiveChannelStore: AlertReceiveChannelStore = new AlertReceiveChannelStore(this);
  outgoingWebhookStore: OutgoingWebhookStore = new OutgoingWebhookStore(this);
  alertReceiveChannelFiltersStore: AlertReceiveChannelFiltersStore = new AlertReceiveChannelFiltersStore(this);
  escalationChainStore: EscalationChainStore = new EscalationChainStore(this);
  escalationPolicyStore: EscalationPolicyStore = new EscalationPolicyStore(this);
  teamStore: TeamStore = new TeamStore(this);
  telegramChannelStore: TelegramChannelStore = new TelegramChannelStore(this);
  slackStore: SlackStore = new SlackStore(this);
  slackChannelStore: SlackChannelStore = new SlackChannelStore(this);
  heartbeatStore: HeartbeatStore = new HeartbeatStore(this);
  maintenanceStore: MaintenanceStore = new MaintenanceStore(this);
  scheduleStore: ScheduleStore = new ScheduleStore(this);
  userGroupStore: UserGroupStore = new UserGroupStore(this);
  alertGroupStore: AlertGroupStore = new AlertGroupStore(this);
  resolutionNotesStore: ResolutionNotesStore = new ResolutionNotesStore(this);
  apiTokenStore: ApiTokenStore = new ApiTokenStore(this);
  OrganizationLogStore: OrganizationLogStore = new OrganizationLogStore(this);
  globalSettingStore: GlobalSettingStore = new GlobalSettingStore(this);
  matrixStore: MatrixStore = new MatrixStore(this);
  // stores

  async updateBasicData() {
    return Promise.all([
      this.teamStore.loadCurrentTeam(),
      this.grafanaTeamStore.updateItems(),
      this.updateFeatures(),
      this.userStore.updateNotificationPolicyOptions(),
      this.userStore.updateNotifyByOptions(),
      this.alertReceiveChannelStore.updateAlertReceiveChannelOptions(),
      this.alertReceiveChannelStore.updateAlertReceiveChannelOptions(),
      this.escalationPolicyStore.updateWebEscalationPolicyOptions(),
      this.escalationPolicyStore.updateEscalationPolicyOptions(),
      this.escalationPolicyStore.updateNumMinutesInWindowOptions(),
    ]);
  }

  setupPluginError(errorMsg: string) {
    this.appLoading = false;
    this.initializationError = errorMsg;
  }

  /**
   * First check to see if the plugin has been provisioned (plugin's meta jsonData has an onCallApiUrl saved)
   * If not, tell the user they first need to configure/provision the plugin.
   *
   * Otherwise, get the plugin connection status from the OnCall API and check a few pre-conditions:
   * - plugin must be considered installed by the OnCall API
   * - user must be not "anonymous" (this is determined by the plugin-proxy)
   * - the OnCall API must be currently allowing signup
   * - the user must have an Admin role
   * If these conditions are all met then trigger a data sync w/ the OnCall backend and poll its response
   * Finally, try to load the current user from the OnCall backend
   */
  async setupPlugin(meta: OnCallAppPluginMeta) {
    this.appLoading = true;
    this.initializationError = null;
    this.onCallApiUrl = meta.jsonData?.onCallApiUrl;

    if (!this.onCallApiUrl) {
      // plugin is not provisioned
      return this.setupPluginError('🚫 Plugin has not been initialized');
    }

    // at this point we know the plugin is provionsed
    const pluginConnectionStatus = await PluginState.checkIfPluginIsConnected(this.onCallApiUrl);
    if (typeof pluginConnectionStatus === 'string') {
      return this.setupPluginError(pluginConnectionStatus);
    }

    const { allow_signup, is_installed, is_user_anonymous } = pluginConnectionStatus;
    if (is_user_anonymous) {
      return this.setupPluginError(
        '😞 Unfortunately Grafana OnCall is available for authorized users only, please sign in to proceed.'
      );
    } else if (!is_installed) {
      if (!allow_signup) {
        return this.setupPluginError('🚫 OnCall has temporarily disabled signup of new users. Please try again later.');
      }

      if (!contextSrv.hasRole(OrgRole.Admin)) {
        return this.setupPluginError('🚫 Admin must sign on to setup OnCall before a Viewer can use it');
      }

      try {
        /**
         * this will install AND sync the necessary data
         * the sync is done automatically by the /plugin/install OnCall API endpoint
         * therefore there is no need to trigger an additional/separate sync, nor poll a status
         */
        await PluginState.installPlugin();
      } catch (e) {
        return this.setupPluginError(PluginState.getHumanReadableErrorFromOnCallError(e, this.onCallApiUrl, 'install'));
      }
    } else {
      const syncDataResponse = await PluginState.syncDataWithOnCall(this.onCallApiUrl);

      if (typeof syncDataResponse === 'string') {
        return this.setupPluginError(syncDataResponse);
      }

      // everything is all synced successfully at this point..
      this.backendVersion = syncDataResponse.version;
      this.backendLicense = syncDataResponse.license;
    }

    try {
      await this.userStore.loadCurrentUser();
    } catch (e) {
      return this.setupPluginError('OnCall was not able to load the current user. Try refreshing the page');
    }

    this.appLoading = false;
  }

  isUserActionAllowed(action: UserAction) {
    return this.userStore.currentUser && this.userStore.currentUser.permissions.includes(action);
  }

  hasFeature(feature: string | AppFeature) {
    // todo use AppFeature only
    return this.features?.[feature];
  }

  @observable
  async updateFeatures() {
    const response = await makeRequest('/features/', {});
    this.features = response.reduce(
      (acc: any, key: string) => ({
        ...acc,
        [key]: true,
      }),
      {}
    );
  }

  @action
  async removeSlackIntegration() {
    await this.slackStore.removeSlackIntegration();
  }

  @action
  async installSlackIntegration() {
    await this.slackStore.installSlackIntegration();
  }

  async getApiUrlForSettings() {
    const settings = await PluginState.getGrafanaPluginSettings();
    return settings.jsonData?.onCallApiUrl;
  }
}
