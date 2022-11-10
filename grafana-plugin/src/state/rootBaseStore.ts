import { AppPluginMeta } from '@grafana/data';
import { getBackendSrv } from '@grafana/runtime';
import { action, observable } from 'mobx';
import moment from 'moment-timezone';
import qs from 'query-string';
import { OnCallAppSettings } from 'types';

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

import { AppFeature } from './features';
import {
  getPluginSyncStatus,
  installPlugin,
  startPluginSync,
  SYNC_STATUS_RETRY_LIMIT,
  syncStatusDelay,
} from './plugin';
import { UserAction } from './userAction';

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
  pluginIsInitialized = true;

  @observable
  correctProvisioningForInstallation = true;

  @observable
  correctRoleForInstallation = true;

  @observable
  signupAllowedForPlugin = true;

  @observable
  initializationError = '';

  @observable
  retrySync = false;

  @observable
  isUserAnonymous = false;

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
  // stores

  async updateBasicData() {
    this.userStore.loadCurrentUser();
    this.teamStore.loadCurrentTeam();
    this.grafanaTeamStore.updateItems();
    this.updateFeatures();
    this.userStore.updateNotificationPolicyOptions();
    this.userStore.updateNotifyByOptions();
    this.alertReceiveChannelStore.updateAlertReceiveChannelOptions();
    this.alertReceiveChannelStore.updateAlertReceiveChannelOptions();
    this.escalationPolicyStore.updateWebEscalationPolicyOptions();
    this.escalationPolicyStore.updateEscalationPolicyOptions();
    this.escalationPolicyStore.updateNumMinutesInWindowOptions();
  }

  async getUserRole() {
    const user = await getBackendSrv().get('/api/user');
    const userRoles = await getBackendSrv().get('/api/user/orgs');
    const userRole = userRoles.find(
      (userRole: { name: string; orgId: number; role: string }) => userRole.orgId === user.orgId
    );
    return userRole.role;
  }

  async finishSync(get_sync_response: any) {
    if (!get_sync_response.token_ok) {
      this.initializationError = 'OnCall was not able to connect back to this Grafana';
      return;
    }
    this.backendVersion = get_sync_response.version;
    this.backendLicense = get_sync_response.license;
    this.appLoading = false;
  }

  handleSyncException(e: any) {
    this.initializationError = e.response.status;
  }

  async startSync() {
    try {
      return await startPluginSync();
    } catch (e) {
      if (e.response.status === 403) {
        this.correctProvisioningForInstallation = false;
        return;
      } else {
        this.initializationError = e.response.status;
        return;
      }
    }
  }

  resetStatusToDefault() {
    this.appLoading = true;
    this.pluginIsInitialized = true;
    this.correctProvisioningForInstallation = true;
    this.correctRoleForInstallation = true;
    this.signupAllowedForPlugin = true;
    this.initializationError = '';
    this.retrySync = false;
    this.isUserAnonymous = false;
  }

  async waitForSyncStatus(retryCount = 0) {
    if (retryCount > SYNC_STATUS_RETRY_LIMIT) {
      this.retrySync = true;
      return;
    }

    getPluginSyncStatus()
      .then((get_sync_response) => {
        if (get_sync_response.hasOwnProperty('token_ok')) {
          this.finishSync(get_sync_response);
        } else {
          syncStatusDelay(retryCount + 1).then(() => this.waitForSyncStatus(retryCount + 1));
        }
      })
      .catch((e) => {
        this.handleSyncException(e);
      });
  }

  async setupPlugin(meta: AppPluginMeta<OnCallAppSettings>) {
    this.resetStatusToDefault();

    if (!meta.jsonData?.onCallApiUrl) {
      this.pluginIsInitialized = false;
      return;
    }

    this.onCallApiUrl = meta.jsonData.onCallApiUrl;

    let syncStartStatus = await this.startSync();
    if (syncStartStatus.is_user_anonymous) {
      this.isUserAnonymous = true;
      return;
    } else if (!syncStartStatus.is_installed) {
      if (!syncStartStatus.allow_signup) {
        this.signupAllowedForPlugin = false;
        return;
      }
      const userRole = await this.getUserRole();
      if (userRole !== 'Admin') {
        this.correctRoleForInstallation = false;
        return;
      }
      await installPlugin();
    }
    await this.waitForSyncStatus();
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
    const settings = await getBackendSrv().get('/api/plugins/grafana-oncall-app/settings');
    return settings.jsonData?.onCallApiUrl;
  }
}
