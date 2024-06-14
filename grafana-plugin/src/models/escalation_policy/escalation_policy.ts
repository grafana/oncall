import { action, observable, makeObservable, runInAction } from 'mobx';

import { BaseStore } from 'models/base_store';
import { EscalationChain } from 'models/escalation_chain/escalation_chain.types';
import { EscalationPolicy } from 'models/escalation_policy/escalation_policy.types';
import { makeRequest } from 'network/network';
import { move } from 'state/helpers';
import { RootStore } from 'state/rootStore';

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
  webEscalationChoices: any = [];

  constructor(rootStore: RootStore) {
    super(rootStore);

    makeObservable(this);

    this.path = '/escalation_policies/';
  }

  @action.bound
  async updateWebEscalationPolicyOptions() {
    const response = await makeRequest('/escalation_policies/escalation_options/', {});

    runInAction(() => {
      this.webEscalationChoices = response;
    });
  }

  @action.bound
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

    runInAction(() => {
      this.items = {
        ...this.items,
        ...escalationPolicies,
      };

      this.escalationChainToEscalationPolicy = {
        ...this.escalationChainToEscalationPolicy,
        [escalationChainId]: response.map((escalationPolicy: EscalationPolicy) => escalationPolicy.id),
      };
    });
  }

  @action.bound
  createEscalationPolicy(escalationChainId: EscalationChain['id'], data: Partial<EscalationPolicy>) {
    return super.create({
      ...data,
      escalation_chain: escalationChainId,
    });
  }

  @action.bound
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

  @action.bound
  async moveEscalationPolicyToPosition(oldIndex: any, newIndex: any, escalationChainId: EscalationChain['id']) {
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

  @action.bound
  async deleteEscalationPolicy(data: Partial<EscalationPolicy>) {
    const index = this.escalationChainToEscalationPolicy[data.escalation_chain].findIndex(
      (escalationPolicyId: EscalationPolicy['id']) => escalationPolicyId === data.id
    );

    this.escalationChainToEscalationPolicy[data.escalation_chain].splice(index, 1);

    await super.delete(data.id);

    this.updateEscalationPolicies(data.escalation_chain);
  }
}
