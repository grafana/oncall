import { get } from 'lodash-es';
import { action, observable } from 'mobx';

import BaseStore from 'models/base_store';
import { EscalationChain } from 'models/escalation_chain/escalation_chain.types';
import { EscalationPolicy } from 'models/escalation_policy/escalation_policy.types';
import { makeRequest } from 'network';
import { Mixpanel } from 'services/mixpanel';
import { RootStore } from 'state';
import { move } from 'state/helpers';
import { SelectOption } from 'state/types';

export class EscalationPolicyStore extends BaseStore {
  @observable.shallow
  items: { [id: string]: EscalationPolicy } = {};

  @observable
  escalationChainToEscalationPolicy: {
    [id: string]: Array<EscalationPolicy['id']>;
  } = {};

  @observable
  escalationChoices: any = [];

  @observable
  numMinutesInWindowOptions: SelectOption[] = [];

  @observable
  webEscalationChoices: any = [];

  constructor(rootStore: RootStore) {
    super(rootStore);

    this.path = '/escalation_policies/';
  }

  @action
  async updateWebEscalationPolicyOptions() {
    const response = await makeRequest('/escalation_policies/escalation_options/', {});

    this.webEscalationChoices = response;
  }

  @action
  async updateEscalationPolicyOptions() {
    const response = await makeRequest('/escalation_policies/', {
      method: 'OPTIONS',
    });

    this.escalationChoices = get(response, 'actions.POST', []);
  }

  @action
  async updateNumMinutesInWindowOptions() {
    const response = await makeRequest('/escalation_policies/num_minutes_in_window_options/', {});

    this.numMinutesInWindowOptions = response;
  }

  @action
  async updateEscalationPolicies(escalationChainId: EscalationChain['id']) {
    const response = await makeRequest(this.path, {
      params: { escalation_chain: escalationChainId },
    });

    const escalationPolicies = response.reduce(
      (acc: any, escalationPolicy: EscalationPolicy) => ({
        ...acc,
        [escalationPolicy.id]: escalationPolicy,
      }),
      {}
    );

    this.items = {
      ...this.items,
      ...escalationPolicies,
    };

    this.escalationChainToEscalationPolicy = {
      ...this.escalationChainToEscalationPolicy,
      [escalationChainId]: response.map((escalationPolicy: EscalationPolicy) => escalationPolicy.id),
    };
  }

  @action
  createEscalationPolicy(escalationChainId: EscalationChain['id'], data: Partial<EscalationPolicy>) {
    return super.create({
      ...data,
      escalation_chain: escalationChainId,
    });
  }

  @action
  async saveEscalationPolicy(id: EscalationPolicy['id'], data: Partial<EscalationPolicy>) {
    this.items[id] = {
      ...this.items[id],
      ...data,
    };

    await super.update(id, data);

    if (data.escalation_chain) {
      this.updateEscalationPolicies(data.escalation_chain);
    }
  }

  @action
  async moveEscalationPolicyToPosition(oldIndex: any, newIndex: any, escalationChainId: EscalationChain['id']) {
    Mixpanel.track('Move EscalationPolicy', null);

    const escalationPolicyId = this.escalationChainToEscalationPolicy[escalationChainId][oldIndex];

    this.escalationChainToEscalationPolicy[escalationChainId] = move(
      this.escalationChainToEscalationPolicy[escalationChainId],
      oldIndex,
      newIndex
    );

    await makeRequest(`/escalation_policies/${escalationPolicyId}/move_to_position/?position=${newIndex}`, {
      method: 'PUT',
    });

    this.updateEscalationPolicies(escalationChainId);
  }

  @action
  async deleteEscalationPolicy(data: Partial<EscalationPolicy>) {
    const index = this.escalationChainToEscalationPolicy[data.escalation_chain].findIndex(
      (escalationPolicyId: EscalationPolicy['id']) => escalationPolicyId === data.id
    );

    this.escalationChainToEscalationPolicy[data.escalation_chain].splice(index, 1);

    await super.delete(data.id);

    this.updateEscalationPolicies(data.escalation_chain);
  }
}
