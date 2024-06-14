import { contextSrv } from 'grafana/app/core/core';
import { action, computed, makeObservable, observable, runInAction } from 'mobx';
import qs from 'query-string';
import { OnCallAppPluginMeta } from 'types';

import { AlertReceiveChannelStore } from 'models/alert_receive_channel/alert_receive_channel';
import { AlertReceiveChannelConnectedChannelsStore } from 'models/alert_receive_channel_connected_channels/alert_receive_channel_connected_channels';
import { AlertReceiveChannelFiltersStore } from 'models/alert_receive_channel_filters/alert_receive_channel_filters';
import { AlertReceiveChannelWebhooksStore } from 'models/alert_receive_channel_webhooks/alert_receive_channel_webhooks';
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
import { LabelStore } from 'models/label/label';
import { LoaderStore } from 'models/loader/loader';
import { MSTeamsChannelStore } from 'models/msteams_channel/msteams_channel';
import { OrganizationStore } from 'models/organization/organization';
import { OutgoingWebhookStore } from 'models/outgoing_webhook/outgoing_webhook';
import { ResolutionNotesStore } from 'models/resolution_note/resolution_note';
import { ScheduleStore } from 'models/schedule/schedule';
import { SlackStore } from 'models/slack/slack';
import { SlackChannelStore } from 'models/slack_channel/slack_channel';
import { TelegramChannelStore } from 'models/telegram_channel/telegram_channel';
import { TimezoneStore } from 'models/timezone/timezone';
import { UserStore } from 'models/user/user';
import { UserGroupStore } from 'models/user_group/user_group';
import { makeRequest } from 'network/network';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { AppFeature } from 'state/features';
import { PluginState } from 'state/plugin/plugin';
import { retryFailingPromises } from 'utils/async';
import {
  APP_VERSION,
  CLOUD_VERSION_REGEX,
  getOnCallApiUrl,
  GRAFANA_LICENSE_CLOUD,
  GRAFANA_LICENSE_OSS,
} from 'utils/consts';

// ------ Dashboard ------ //

export class RootBaseStore {
  @observable
  isBasicDataLoaded = false;

  @observable
  backendVersion = '';

  @observable
  backendLicense = '';

  @observable
  recaptchaSiteKey = '';

  @observable
  initializationError = '';

  @observable
  currentlyUndergoingMaintenance = false;

  @observable
  isMobile = false;

  initialQuery = qs.parse(window.location.search);

  @observable
  selectedAlertReceiveChannel?: ApiSchemas['AlertReceiveChannel']['id'];

  @observable
  features?: { [key: string]: boolean };

  @observable
  pageTitle = '';

  @observable
  onCallApiUrl: string;

  @observable
  insightsDatasource?: string;

  // stores
  userStore = new UserStore(this);
  cloudStore = new CloudStore(this);
  directPagingStore = new DirectPagingStore(this);
  grafanaTeamStore = new GrafanaTeamStore(this);
  alertReceiveChannelStore = new AlertReceiveChannelStore(this);
  alertReceiveChannelConnectedChannelsStore = new AlertReceiveChannelConnectedChannelsStore(this);
  alertReceiveChannelWebhooksStore = new AlertReceiveChannelWebhooksStore(this);
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
  labelsStore = new LabelStore(this);
  timezoneStore = new TimezoneStore(this);
  msteamsChannelStore: MSTeamsChannelStore = new MSTeamsChannelStore(this);
  loaderStore = LoaderStore;

  constructor() {
    makeObservable(this);
  }
  @action.bound
  loadBasicData = async () => {
    const updateFeatures = async () => {
      await this.updateFeatures();

      // Only fetch cloud connection status when cloud connection feature is enabled on OSS instance
      // Note that this.hasFeature can only be called after this.updateFeatures()
      if (this.hasFeature(AppFeature.CloudConnection)) {
        await this.cloudStore.loadCloudConnectionStatus();
      }
    };

    await retryFailingPromises([
      () => this.userStore.loadCurrentUser(),
      () => this.organizationStore.loadCurrentOrganization(),
      () => this.grafanaTeamStore.updateItems(),
      () => updateFeatures(),
      () => this.alertReceiveChannelStore.fetchAlertReceiveChannelOptions(),
    ]);
    this.setIsBasicDataLoaded(true);
  };

  @action
  loadMasterData = async () => {
    Promise.all([this.userStore.updateNotificationPolicyOptions(), this.userStore.updateNotifyByOptions()]);
  };

  @action
  setIsBasicDataLoaded(value: boolean) {
    this.isBasicDataLoaded = value;
  }

  @action
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
    this.setupPluginError(null);
    this.onCallApiUrl = getOnCallApiUrl(meta);
    this.insightsDatasource = meta.jsonData?.insightsDatasource || 'grafanacloud-usage';

    if (!this.onCallApiUrl) {
      // plugin is not provisioned
      return this.setupPluginError('🚫 Plugin has not been initialized');
    }

    if (this.isOpenSource && !meta.secureJsonFields?.onCallApiToken) {
      // Reinstall plugin if onCallApiToken is missing
      const errorMsg = await PluginState.selfHostedInstallPlugin(this.onCallApiUrl, true);
      if (errorMsg) {
        return this.setupPluginError(errorMsg);
      }
      location.reload();
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
        } catch (e) {
          return this.setupPluginError(
            PluginState.getHumanReadableErrorFromOnCallError(e, this.onCallApiUrl, 'install')
          );
        }
      } else {
        if (contextSrv.licensedAccessControlEnabled()) {
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
      runInAction(() => {
        this.backendVersion = pluginConnectionStatus.version;
        this.backendLicense = pluginConnectionStatus.license;
        this.recaptchaSiteKey = pluginConnectionStatus.recaptcha_site_key;
      });
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
    const setupRequiredPermissions = [
      'plugins:write',
      'org.users:read',
      'teams:read',
      'apikeys:create',
      'apikeys:delete',
    ];
    return setupRequiredPermissions.filter(function (permission) {
      return !contextSrv.hasPermission(permission);
    });
  }

  // todo use AppFeature only
  hasFeature = (feature: string | AppFeature) => this.features?.[feature];

  get license() {
    if (this.backendLicense) {
      return this.backendLicense;
    }
    if (CLOUD_VERSION_REGEX.test(APP_VERSION)) {
      return GRAFANA_LICENSE_CLOUD;
    }
    return GRAFANA_LICENSE_OSS;
  }

  @computed
  get isOpenSource(): boolean {
    return this.license === GRAFANA_LICENSE_OSS;
  }

  @action.bound
  async updateFeatures() {
    const response = await makeRequest('/features/', {});

    runInAction(() => {
      this.features = response.reduce(
        (acc: any, key: string) => ({
          ...acc,
          [key]: true,
        }),
        {}
      );
    });
  }

  @action.bound
  setPageTitle(title: string) {
    this.pageTitle = title;
  }

  @action
  async removeSlackIntegration() {
    await this.slackStore.removeSlackIntegration();
  }

  @action
  async installSlackIntegration() {
    await this.slackStore.installSlackIntegration();
  }

  @action.bound
  async getApiUrlForSettings() {
    return this.onCallApiUrl;
  }
}
