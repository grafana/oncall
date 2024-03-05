import React from 'react';

import { pick } from 'lodash-es';

import { User } from './user.types';
import { onCallApi } from 'network/oncall-api/http-client';

export class UserHelper {
  static getTimezone(user: Pick<User, 'timezone'>) {
    return user.timezone || 'UTC';
  }

  static getUserNotificationsSummary(user: User) {
    if (!user) {
      return null;
    }

    return (
      <>
        Default: {user?.notification_chain_verbal?.default}
        <br />
        Important: {user?.notification_chain_verbal?.important}
      </>
    );
  }

  static prepareForUpdate(user: User) {
    return pick(user, ['pk', 'email']);
  }

  /**
   * NOTE: if is_currently_oncall=all the backend will not paginate the results, it will send back an array of ALL users
   */
  static async search(f: any = { searchTerm: '' }, page = 1) {
    const filters = typeof f === 'string' ? { searchTerm: f } : f; // for GSelect compatibility
    const { searchTerm: search, ...restFilters } = filters;
    return (await onCallApi().GET('/users/', { params: { query: { search, page, ...restFilters } } })).data;
  }

  getSearchResult = () => {
    return {
      page_size: this.searchResult.page_size,
      count: this.searchResult.count,
      results: this.searchResult.results?.map((userPk: User['pk']) => this.items?.[userPk]),
    };
  };

  sendTelegramConfirmationCode = async (userPk: User['pk']) => {
    return await makeRequest(`/users/${userPk}/get_telegram_verification_code/`, {});
  };

  sendBackendConfirmationCode = (userPk: User['pk'], backend: string) =>
    makeRequest<string>(`/users/${userPk}/get_backend_verification_code?backend=${backend}`, {
      method: 'GET',
    });

  @action.bound
  async fetchVerificationCode(userPk: User['pk'], recaptchaToken: string) {
    await makeRequest(`/users/${userPk}/get_verification_code/`, {
      method: 'GET',
      headers: { 'X-OnCall-Recaptcha': recaptchaToken },
    }).catch(throttlingError);
  }

  @action.bound
  async fetchVerificationCall(userPk: User['pk'], recaptchaToken: string) {
    await makeRequest(`/users/${userPk}/get_verification_call/`, {
      method: 'GET',
      headers: { 'X-OnCall-Recaptcha': recaptchaToken },
    }).catch(throttlingError);
  }

  @action.bound
  async verifyPhone(userPk: User['pk'], token: string) {
    return await makeRequest(`/users/${userPk}/verify_number/?token=${token}`, {
      method: 'PUT',
    }).catch(throttlingError);
  }

  @action.bound
  async forgetPhone(userPk: User['pk']) {
    return await makeRequest(`/users/${userPk}/forget_number/`, {
      method: 'PUT',
    });
  }

  async getiCalLink(userPk: User['pk']) {
    return await makeRequest(`/users/${userPk}/export_token/`, {
      method: 'GET',
    });
  }

  async createiCalLink(userPk: User['pk']) {
    return await makeRequest(`/users/${userPk}/export_token/`, {
      method: 'POST',
    });
  }

  async deleteiCalLink(userPk: User['pk']) {
    await makeRequest(`/users/${userPk}/export_token/`, {
      method: 'DELETE',
    });
  }
}
