import { action, observable, makeObservable, runInAction } from 'mobx';

import { BaseStore } from 'models/base_store';
import { SlackChannel } from 'models/slack_channel/slack_channel.types';
import { makeRequest, makeRequestRaw } from 'network/network';
import { RootStore } from 'state/rootStore';
import { GENERIC_ERROR } from 'utils/consts';
import { openErrorNotification } from 'utils/utils';

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

  @action.bound
  async updateSlackSettings() {
    const result = await makeRequest('/slack_settings/', {});

    runInAction(() => {
      this.slackSettings = result;
    });
  }

  @action.bound
  async saveSlackSettings(data: Partial<SlackSettings>) {
    const result = await makeRequest('/slack_settings/', {
      data,
      method: 'PUT',
    });

    runInAction(() => {
      this.slackSettings = result;
    });
  }

  @action.bound
  async setGeneralLogChannelId(id: SlackChannel['id']) {
    return await makeRequest('/set_general_channel/', {
      method: 'POST',
      data: { id },
    });
  }

  @action.bound
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
    try {
      return await makeRequest('/slack_integration/', {
        validateStatus: function (status) {
          return status === 200 || status === 403;
        },
        method: 'POST',
        params: { slack_id },
      });
    } catch (err) {
      this.onApiError(err);
    }
  }

  async slackLogin() {
    const url_for_redirect = await makeRequest('/login/slack-login/', {});
    window.location = url_for_redirect;
  }

  async installSlackIntegration() {
    try {
      const response = await makeRequestRaw('/login/slack-install-free/', {});

      if (response.status === 201) {
        this.rootStore.organizationStore.loadCurrentOrganization();
      } else if (response.status === 200) {
        window.location = response.data;
      }
    } catch (ex) {
      if (ex.response?.status === 500) {
        openErrorNotification(GENERIC_ERROR);
      }
    }
  }

  async removeSlackIntegration() {
    return await makeRequest('/slack/reset_slack/', { method: 'POST' });
  }
}
