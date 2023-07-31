import { OrgRole } from '@grafana/data';
import { locationService } from '@grafana/runtime';
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
import { DirectPagingStore } from 'models/direct_paging/direct_paging';
import { EscalationChainStore } from 'models/escalation_chain/escalation_chain';
import { EscalationPolicyStore } from 'models/escalation_policy/escalation_policy';
import { FiltersStore } from 'models/filters/filters';
import { GlobalSettingStore } from 'models/global_setting/global_setting';
import { GrafanaTeamStore } from 'models/grafana_team/grafana_team';
import { HeartbeatStore } from 'models/heartbeat/heartbeat';
import { OrganizationStore } from 'models/organization/organization';
import { OutgoingWebhookStore } from 'models/outgoing_webhook/outgoing_webhook';
import { ResolutionNotesStore } from 'models/resolution_note/resolution_note';
import { ScheduleStore } from 'models/schedule/schedule';
import { SlackStore } from 'models/slack/slack';
import { SlackChannelStore } from 'models/slack_channel/slack_channel';
import { TelegramChannelStore } from 'models/telegram_channel/telegram_channel';
import { Timezone } from 'models/timezone/timezone.types';
import { UserStore } from 'models/user/user';
import { UserGroupStore } from 'models/user_group/user_group';
import { makeRequest } from 'network';
import { AppFeature } from 'state/features';
import PluginState from 'state/plugin';
import {
  APP_VERSION,
  CLOUD_VERSION_REGEX,
  GRAFANA_LICENSE_CLOUD,
  GRAFANA_LICENSE_OSS,
  PLUGIN_ROOT,
} from 'utils/consts';
import FaroHelper from 'utils/faro';

// ------ Dashboard ------ //

export class RootBaseStore {
  @observable
  currentTimezone: Timezone = moment.tz.guess() as Timezone;

  @observable
  backendVersion = '';

  @observable
  backendLicense = '';

  @observable
  recaptchaSiteKey = '';

  @observable
  initializationError = null;

  @observable
  currentlyUndergoingMaintenance = false;

  @observable
  isMobile = false;

  initialQuery = qs.parse(window.location.search);

  @observable
  selectedAlertReceiveChannel?: AlertReceiveChannel['id'];

  @observable
  features?: { [key: string]: boolean };

  @observable
  incidentFilters: any;

  @observable
  incidentsPage: any = this.initialQuery.p ? Number(this.initialQuery.p) : 1;

  @observable
  onCallApiUrl: string;

  // --------------------------
  userStore = new UserStore(this);
  cloudStore = new CloudStore(this);
  directPagingStore = new DirectPagingStore(this);
  grafanaTeamStore = new GrafanaTeamStore(this);
  alertReceiveChannelStore = new AlertReceiveChannelStore(this);
  outgoingWebhookStore = new OutgoingWebhookStore(this);
  alertReceiveChannelFiltersStore = new AlertReceiveChannelFiltersStore(this);
  escalationChainStore = new EscalationChainStore(this);
  escalationPolicyStore = new EscalationPolicyStore(this);
  organizationStore = new OrganizationStore(this);
  telegramChannelStore = new TelegramChannelStore(this);
  slackStore = new SlackStore(this);
  slackChannelStore = new SlackChannelStore(this);
  heartbeatStore = new HeartbeatStore(this);
  scheduleStore = new ScheduleStore(this);
  userGroupStore = new UserGroupStore(this);
  alertGroupStore = new AlertGroupStore(this);
  resolutionNotesStore = new ResolutionNotesStore(this);
  apiTokenStore = new ApiTokenStore(this);
  globalSettingStore = new GlobalSettingStore(this);
  filtersStore = new FiltersStore(this);

  // stores

  async updateBasicData() {
    const updateFeatures = async () => {
      await this.updateFeatures();

      // Only fetch cloud connection status when cloud connection feature is enabled on OSS instance
      // Note that this.hasFeature can only be called after this.updateFeatures()
      if (this.hasFeature(AppFeature.CloudConnection)) {
        await this.cloudStore.loadCloudConnectionStatus();
      }
    };

    return Promise.all([
      this.userStore.loadCurrentUser(),
      this.organizationStore.loadCurrentOrganization(),
      this.grafanaTeamStore.updateItems(),
      updateFeatures(),
      this.userStore.updateNotificationPolicyOptions(),
      this.userStore.updateNotifyByOptions(),
      this.alertReceiveChannelStore.updateAlertReceiveChannelOptions(),
      this.escalationPolicyStore.updateWebEscalationPolicyOptions(),
      this.escalationPolicyStore.updateEscalationPolicyOptions(),
      this.escalationPolicyStore.updateNumMinutesInWindowOptions(),
      this.alertGroupStore.fetchIRMPlan(),
    ]);
  }

  setupPluginError(errorMsg: string) {
    this.initializationError = errorMsg;
  }

  /**
   * This function is called in the background when the plugin is loaded.
   * It will check the status of the plugin and
   * rerender the screen with the appropriate message if the plugin is not setup correctly.
   *
   * First check to see if the plugin has been provisioned (plugin's meta jsonData has an onCallApiUrl saved)
   * If not, tell the user they first need to configure/provision the plugin.
   *
   * Otherwise, get the plugin connection status from the OnCall API and check a few pre-conditions:
   * - OnCall api should not be under maintenance
   * - plugin must be considered installed by the OnCall API
   * - token_ok must be true
   *   - This represents the status of the Grafana API token. It can be false in the event that either the token
   *   hasn't been created, or if the API token was revoked in Grafana.
   * - user must be not "anonymous" (this is determined by the plugin-proxy)
   * - the OnCall API must be currently allowing signup
   * - the user must have an Admin role and necessary permissions
   * Finally, try to load the current user from the OnCall backend
   */
  async setupPlugin(meta: OnCallAppPluginMeta) {
    this.initializationError = null;
    this.onCallApiUrl = meta.jsonData?.onCallApiUrl;

    if (!FaroHelper.faro) {
      FaroHelper.initializeFaro(this.onCallApiUrl);
    }

    if (!this.onCallApiUrl) {
      // plugin is not provisioned
      return this.setupPluginError('🚫 Plugin has not been initialized');
    }

    // at this point we know the plugin is provisioned
    const pluginConnectionStatus = await PluginState.updatePluginStatus(this.onCallApiUrl);
    if (typeof pluginConnectionStatus === 'string') {
      return this.setupPluginError(pluginConnectionStatus);
    }

    // Check if the plugin is currently undergoing maintenance
    if (pluginConnectionStatus.currently_undergoing_maintenance_message) {
      this.currentlyUndergoingMaintenance = true;
      return this.setupPluginError(`🚧 ${pluginConnectionStatus.currently_undergoing_maintenance_message} 🚧`);
    }

    const { allow_signup, is_installed, is_user_anonymous, token_ok } = pluginConnectionStatus;

    // Anonymous users are not allowed to use the plugin
    if (is_user_anonymous) {
      return this.setupPluginError(
        '😞 Grafana OnCall is available for authorized users only, please sign in to proceed.'
      );
    }
    // If the plugin is not installed in the OnCall backend, or token is not valid, then we need to install it
    if (!is_installed || !token_ok) {
      if (!allow_signup) {
        return this.setupPluginError('🚫 OnCall has temporarily disabled signup of new users. Please try again later.');
      }
      const missingPermissions = this.checkMissingSetupPermissions();
      if (missingPermissions.length === 0) {
        try {
          /**
           * this will install AND sync the necessary data
           * the sync is done automatically by the /plugin/install OnCall API endpoint
           * therefore there is no need to trigger an additional/separate sync, nor poll a status
           */
          await PluginState.installPlugin();
          locationService.push(PLUGIN_ROOT);
        } catch (e) {
          return this.setupPluginError(
            PluginState.getHumanReadableErrorFromOnCallError(e, this.onCallApiUrl, 'install')
          );
        }
      } else {
        if (contextSrv.accessControlEnabled()) {
          return this.setupPluginError(
            '🚫 User is missing permission(s) ' +
              missingPermissions.join(', ') +
              ' to setup OnCall before it can be used'
          );
        } else {
          return this.setupPluginError(
            '🚫 User with Admin permissions in your organization must sign on and setup OnCall before it can be used'
          );
        }
      }
    } else {
      // everything is all synced successfully at this point..
      this.backendVersion = pluginConnectionStatus.version;
      this.backendLicense = pluginConnectionStatus.license;
      this.recaptchaSiteKey = pluginConnectionStatus.recaptcha_site_key;
    }

    if (!this.userStore.currentUser) {
      try {
        await this.userStore.loadCurrentUser();
      } catch (e) {
        return this.setupPluginError('OnCall was not able to load the current user. Try refreshing the page');
      }
    }
  }

  checkMissingSetupPermissions() {
    const fallback = contextSrv.user.orgRole === OrgRole.Admin && !contextSrv.accessControlEnabled();
    const setupRequiredPermissions = [
      'plugins:write',
      'org.users:read',
      'teams:read',
      'apikeys:create',
      'apikeys:delete',
    ];
    return setupRequiredPermissions.filter(function (permission) {
      return !contextSrv.hasAccess(permission, fallback);
    });
  }

  hasFeature(feature: string | AppFeature) {
    // todo use AppFeature only
    return this.features?.[feature];
  }

  get license() {
    if (this.backendLicense) {
      return this.backendLicense;
    }
    if (CLOUD_VERSION_REGEX.test(APP_VERSION)) {
      return GRAFANA_LICENSE_CLOUD;
    }
    return GRAFANA_LICENSE_OSS;
  }

  isOpenSource(): boolean {
    return this.license === GRAFANA_LICENSE_OSS;
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
