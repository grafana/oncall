import { action, observable } from 'mobx';

import BaseStore from 'models/base_store';
import { makeRequest } from 'network';
import { Mixpanel } from 'services/mixpanel';
import { RootStore } from 'state';
import { openErrorNotification } from 'utils';
import { getPathnameByTeamNameSlug, getTeamNameSlugFromUrl } from 'utils/url';

import { Team } from './team.types';

export class TeamStore extends BaseStore {
  @observable
  redirectingToProperTeam = false;

  @observable.shallow
  teams: { [id: number]: Team[] } = {};

  @observable
  currentTeam?: Team;

  constructor(rootStore: RootStore) {
    super(rootStore);

    this.path = '/team/';
  }

  @action
  async loadCurrentTeam() {
    this.currentTeam = await makeRequest('/current_team/', {});
  }

  @action
  async setCurrentTeam(teamId: Team['pk']) {
    this.redirectingToProperTeam = true;

    const team = await makeRequest(`/current_team/`, {
      method: 'POST',
      data: { team_id: teamId },
    });

    const pathName = getPathnameByTeamNameSlug(team.name_slug);

    window.location.pathname = pathName;
  }

  @action
  async addTeam(data: Partial<Team>) {
    let createdTeam;
    try {
      createdTeam = await makeRequest('/teams/', {
        method: 'POST',
        data,
      });
    } catch (e) {
      openErrorNotification(e.response.data);
      return;
    }

    this.setCurrentTeam(createdTeam.pk);

    Mixpanel.track('Add Team', null);
  }

  @action
  async saveCurrentTeam(data: any) {
    this.currentTeam = await makeRequest('/current_team/', {
      method: 'PUT',
      data,
    });
  }

  @action
  async justSaveCurrentTeam(data: any) {
    return await makeRequest('/current_team/', {
      method: 'PUT',
      data,
    });
  }

  @action
  async getTelegramVerificationCode(pk: Team['pk']) {
    const response = await makeRequest(`/teams/${pk}/get_telegram_verification_code/`, {
      withCredentials: true,
    });

    return response;
  }

  @action
  async unlinkTelegram(pk: Team['pk']) {
    const response = await makeRequest(`/teams/${pk}/unlink_telegram/`, {
      method: 'POST',
      withCredentials: true,
    });

    return response;
  }

  @action
  async getInvitationLink() {
    const response = await makeRequest('/invitation_link/', {
      withCredentials: true,
    });

    return response;
  }

  @action
  async joinToTeam(invitation_token: string) {
    const response = await makeRequest('/join_to_team/', {
      method: 'POST',
      params: { invitation_token, token: invitation_token },
      withCredentials: true,
    });

    return response;
  }

  @action
  async updateTeam(teamId: Team['pk']) {
    const response = await makeRequest(this.path, {
      params: {},
      withCredentials: true,
    });
  }
}
