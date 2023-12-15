import { action, observable, makeObservable, runInAction } from 'mobx';

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
    makeObservable(this);
  }

  @action
  async updateSlackSettings() {
    const result = await makeRequest('/slack_settings/', {});

    runInAction(() => {
      this.slackSettings = result;
    });
  }

  @action
  async saveSlackSettings(data: Partial<SlackSettings>) {
    const result = await makeRequest('/slack_settings/', {
      data,
      method: 'PUT',
    });

    runInAction(() => {
      this.slackSettings = result;
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
    const result = await makeRequest('/slack_integration/', {
      params: { slack_id },
    });

    runInAction(() => {
      this.slackIntegrationData = result;
    });

    return result;
  }

  async reinstallSlackIntegration(slack_id: string) {
    return await makeRequest('/slack_integration/', {
      validateStatus: function (status) {
        return status === 200 || status === 403;
      },
      method: 'POST',
      params: { slack_id },
    }).catch(this.onApiError);
  }

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
