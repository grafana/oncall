import React from 'react';

import { pick } from 'lodash-es';

import { User } from './user.types';
import { onCallApi } from 'network/oncall-api/http-client';
import { UserStore } from './user';
import { throttlingError } from 'utils/utils';
import { ApiSchemas } from 'network/oncall-api/api.types';

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

  static getSearchResult(userStore: UserStore) {
    return {
      page_size: userStore.searchResult.page_size,
      count: userStore.searchResult.count,
      results: userStore.searchResult.results?.map((userPk: ApiSchemas['User']['pk']) => userStore.items?.[userPk]),
    };
  }

  static async sendTelegramConfirmationCode(userPk: ApiSchemas['User']['pk']) {
    return (await onCallApi().GET('/users/{id}/get_telegram_verification_code/', { params: { path: { id: userPk } } }))
      .data;
  }

  static async sendBackendConfirmationCode(userPk: ApiSchemas['User']['pk'], backend: string) {
    return (
      await onCallApi().GET('/users/{id}/get_backend_verification_code/', {
        params: { path: { id: userPk }, query: { backend } },
      })
    ).data;
  }

  static async fetchVerificationCode(userPk: ApiSchemas['User']['pk'], recaptchaToken: string) {
    const { response } = await onCallApi().GET('/users/{id}/get_verification_code/', {
      params: { path: { id: userPk } },
      headers: { 'X-OnCall-Recaptcha': recaptchaToken },
    });

    if (!response.ok) {
      throttlingError(response);
    }
  }

  static async verifyPhone(userPk: ApiSchemas['User']['pk'], token: string) {
    const { response } = await onCallApi().PUT('/users/{id}/verify_number/', {
      params: { path: { id: userPk }, query: { token } },
    });

    if (!response.ok) {
      throttlingError(response);
    }
  }

  @action.bound
  async forgetPhone(userPk: ApiSchemas['User']['pk']) {
    return await makeRequest(`/users/${userPk}/forget_number/`, {
      method: 'PUT',
    });
  }

  async getiCalLink(userPk: ApiSchemas['User']['pk']) {
    return await makeRequest(`/users/${userPk}/export_token/`, {
      method: 'GET',
    });
  }

  async createiCalLink(userPk: ApiSchemas['User']['pk']) {
    return await makeRequest(`/users/${userPk}/export_token/`, {
      method: 'POST',
    });
  }

  async deleteiCalLink(userPk: ApiSchemas['User']['pk']) {
    await makeRequest(`/users/${userPk}/export_token/`, {
      method: 'DELETE',
    });
  }
}
