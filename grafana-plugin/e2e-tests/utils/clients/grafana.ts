import { OrgRole } from '@grafana/data';
import { expect, APIRequestContext } from '@playwright/test';

import { BASE_URL } from '../constants';

type UsersLookupResponse = {
  id: number;
};

type CreateUserResponse = {
  id: number;
};

class GrafanaApiException extends Error {
  constructor(message: string) {
    super(message);
    this.name = this.constructor.name;
  }
}

export default class GrafanaAPIClient {
  userName: string;
  password: string;

  constructor(userName: string, password: string) {
    this.userName = userName;
    this.password = password;
  }

  get requestHeaders() {
    const base64encodedCredentials = Buffer.from(`${this.userName}:${this.password}`).toString('base64');
    return {
      Authorization: `Basic ${base64encodedCredentials}`,
    };
  }

  /**
   * check that the grafana instance is available. If HTTP 503 is returned it means the
   * instance is currently unavailable. Poll until it is available
   */
  pollInstanceUntilItIsHealthy = async (request: APIRequestContext): Promise<boolean> => {
    console.log('Polling the grafana instance to make sure it is healthy');

    const res = await request.get(`${BASE_URL}/api/health`);

    if (!res.ok()) {
      console.log(`Grafana instance is unavailable. Got HTTP ${res.status()}. Will wait 5 seconds and then try again`);
      await new Promise((resolve) => setTimeout(resolve, 5000));
      return this.pollInstanceUntilItIsHealthy(request);
    }
    console.log('Grafana instance is available');
    return true;
  };

  getUserIdByUsername = async (request: APIRequestContext, userName: string): Promise<number> => {
    const res = await request.get(`${BASE_URL}/api/users/lookup?loginOrEmail=${userName}`, {
      headers: this.requestHeaders,
    });
    expect(res.ok()).toBeTruthy();
    const responseData: UsersLookupResponse = await res.json();
    return responseData.id;
  };

  updateUserRole = async (request: APIRequestContext, userId: number, role: OrgRole): Promise<void> => {
    const res = await request.patch(`${BASE_URL}/api/org/users/${userId}`, {
      data: { role },
      headers: this.requestHeaders,
    });
    expect(res.ok()).toBeTruthy();
  };

  /**
   * Should return one of the following two responses:
   * - HTTP 200 - user successfully created
   * - HTTP 412 - user w/ this username already exists (fine to ignore this)
   */
  idempotentlyCreateUserWithRole = async (
    request: APIRequestContext,
    userName: string,
    password: string,
    role: OrgRole
  ) => {
    const res = await request.post(`${BASE_URL}/api/admin/users`, {
      data: {
        name: `e2e user - ${userName}`,
        login: userName,
        password,
      },
    });

    let userId: number;
    const responseCode = res.status();

    if (responseCode === 200) {
      // user was just created
      const respJson: CreateUserResponse = await res.json();
      userId = respJson.id;
    } else if (responseCode == 412) {
      // user already exists, go fetch their user id
      userId = await this.getUserIdByUsername(request, userName);
    } else {
      throw new GrafanaApiException(
        `Received unexpected status code while trying to idempotently create user - HTTP${responseCode}: ${await res.body()}`
      );
    }

    await this.updateUserRole(request, userId, role);
  };

  login = async (request: APIRequestContext, userName: string, password: string) => {
    const res = await request.post(`${BASE_URL}/login`, {
      data: { user: userName, password },
    });
    expect(res.ok()).toBeTruthy();
  };
}
