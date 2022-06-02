import { action, observable } from 'mobx';

import BaseStore from 'models/base_store';
import { SlackChannel } from 'models/slack_channel/slack_channel.types';
import { makeRequest } from 'network';
import { RootStore } from 'state';

import { SlackSettings } from './slack.types';

export class SlackStore extends BaseStore {
  @observable
  slackSettings?: SlackSettings;

  @observable
  slackIntegrationData?: any;

  constructor(rootStore: RootStore) {
    super(rootStore);
  }

  @action
  async updateSlackSettings() {
    this.slackSettings = await makeRequest('/slack_settings/', {});
  }

  @action
  async saveSlackSettings(data: Partial<SlackSettings>) {
    this.slackSettings = await makeRequest('/slack_settings/', {
      data,
      method: 'PUT',
    });
  }

  @action
  async setGeneralLogChannelId(id: SlackChannel['id']) {
    return await makeRequest('/set_general_channel/', {
      method: 'POST',
      data: { id },
    });
  }

  @action
  async updateSlackIntegrationData(slack_id: string) {
    return (this.slackIntegrationData = await makeRequest('/slack_integration/', {
      params: { slack_id },
    }));
  }

  @action
  async reinstallSlackIntegration(slack_id: string) {
    return await makeRequest('/slack_integration/', {
      validateStatus: function (status) {
        return status === 200 || status === 403;
      },
      method: 'POST',
      params: { slack_id },
    }).catch(this.onApiError);
  }

  @action
  async slackLogin() {
    const url_for_redirect = await makeRequest('/login/slack-login/', {});
    window.location = url_for_redirect;
  }

  async installSlackIntegration() {
    const url_for_redirect = await makeRequest('/login/slack-install-free/', {});
    window.location = url_for_redirect;
  }

  async removeSlackIntegration() {
    return await makeRequest('/slack/reset_slack/', { method: 'POST' });
  }
}
