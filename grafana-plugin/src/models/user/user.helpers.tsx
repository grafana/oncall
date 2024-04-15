import React from 'react';

import { pick } from 'lodash-es';

import { ApiSchemas } from 'network/oncall-api/api.types';
import { onCallApi } from 'network/oncall-api/http-client';
import { throttlingError } from 'utils/utils';

import { UserStore } from './user';

export class UserHelper {
  static getTimezone(user: Pick<ApiSchemas['User'], 'timezone'>) {
    return user.timezone || 'UTC';
  }

  static getUserNotificationsSummary(user: ApiSchemas['User']) {
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

  static prepareForUpdate(user: ApiSchemas['User']) {
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

  static async fetchTelegramConfirmationCode(userPk: ApiSchemas['User']['pk']) {
    return (await onCallApi().GET('/users/{id}/get_telegram_verification_code/', { params: { path: { id: userPk } } }))
      .data;
  }

  static async fetchBackendConfirmationCode(userPk: ApiSchemas['User']['pk'], backend: string) {
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
    throttlingError(response);
  }

  static async fetchVerificationCall(userPk: ApiSchemas['User']['pk'], recaptchaToken: string) {
    const { response } = await onCallApi().GET('/users/{id}/get_verification_call/', {
      params: { path: { id: userPk } },
      headers: { 'X-OnCall-Recaptcha': recaptchaToken },
    });
    throttlingError(response);
  }

  static async verifyPhone(userPk: ApiSchemas['User']['pk'], token: string) {
    const { response } = await onCallApi().PUT('/users/{id}/verify_number/', {
      params: { path: { id: userPk }, query: { token } },
    });
    throttlingError(response);
  }

  static async forgetPhone(userPk: ApiSchemas['User']['pk']) {
    return (await onCallApi().PUT('/users/{id}/forget_number/', { params: { path: { id: userPk } } })).data;
  }

  static async getiCalLink(userPk: ApiSchemas['User']['pk']) {
    return (
      await onCallApi({ skipErrorHandling: true }).GET('/users/{id}/export_token/', {
        params: { path: { id: userPk } },
      })
    ).data;
  }

  static async createiCalLink(userPk: ApiSchemas['User']['pk']) {
    return (await onCallApi().POST('/users/{id}/export_token/', { params: { path: { id: userPk } } })).data;
  }

  static async deleteiCalLink(userPk: ApiSchemas['User']['pk']) {
    return (await onCallApi().DELETE('/users/{id}/export_token/', { params: { path: { id: userPk } } })).data;
  }

  static async sendTestPushNotification(userId: ApiSchemas['User']['pk'], isCritical: boolean) {
    return (
      await onCallApi().POST('/users/{id}/send_test_push/', {
        params: { path: { id: userId }, query: { critical: isCritical } },
      })
    ).data;
  }

  static async handleConnectGoogle() {
    const { data } = await onCallApi().GET('/login/{backend}', { params: { path: { backend: 'google-oauth2' } } });
    window.location = data;
  }
}
