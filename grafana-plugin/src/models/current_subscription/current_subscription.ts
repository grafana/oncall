import { action, observable } from 'mobx';

import BaseStore from 'models/base_store';
import { makeRequest } from 'network';
import { RootStore } from 'state';

import { Subscription } from './current_subscription.types';

export class CurrentSubscriptionStore extends BaseStore {
  @observable
  currentSubscription?: Subscription;

  constructor(rootStore: RootStore) {
    super(rootStore);

    this.path = '/current_subscription/';
  }

  @action
  async updateCurrentSubscription() {
    this.currentSubscription = await makeRequest(this.path, {});
  }
}
