import { OnCallAppPluginMeta } from 'app-types';
import { retryFailingPromises } from 'helpers/async';
import { loadJs } from 'helpers/loadJs';
import { action, makeObservable, observable, runInAction } from 'mobx';
import qs from 'query-string';

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
import { MattermostStore } from 'models/mattermost/mattermost';
import { MSTeamsChannelStore } from 'models/msteams_channel/msteams_channel';
import { OrganizationStore } from 'models/organization/organization';
import { OutgoingWebhookStore } from 'models/outgoing_webhook/outgoing_webhook';
import { PluginStore } from 'models/plugin/plugin';
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

// ------ Dashboard ------ //

export class RootBaseStore {
  @observable
  isBasicDataLoaded = false;

  @observable
  recaptchaSiteKey = '';

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
  insightsDatasource = 'grafanacloud-usage';

  // stores
  pluginStore = new PluginStore(this);
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
  mattermostStore = new MattermostStore(this);
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
      () => this.organizationStore.loadCurrentOrganizationConfigChecks(),
      () => this.grafanaTeamStore.updateItems(),
      () => updateFeatures(),
      () => this.alertReceiveChannelStore.fetchAlertReceiveChannelOptions(),
    ]);
    this.setIsBasicDataLoaded(true);
  };

  @action
  setupInsightsDatasource = ({ jsonData: { insightsDatasource } }: OnCallAppPluginMeta) => {
    if (insightsDatasource) {
      this.insightsDatasource = insightsDatasource;
    }
  };

  @action
  loadMasterData = async () => {
    Promise.all([this.userStore.updateNotificationPolicyOptions(), this.userStore.updateNotifyByOptions()]);
  };

  @action
  setIsBasicDataLoaded(value: boolean) {
    this.isBasicDataLoaded = value;
  }

  // todo use AppFeature only
  hasFeature = (feature: string | AppFeature) => this.features?.[feature];

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

  @action.bound
  async loadRecaptcha() {
    const { recaptcha_site_key } = await makeRequest<{ recaptcha_site_key: string }>('/plugin/recaptcha');
    this.recaptchaSiteKey = recaptcha_site_key;
    loadJs(`https://www.google.com/recaptcha/api.js?render=${recaptcha_site_key}`, recaptcha_site_key);
  }
}
