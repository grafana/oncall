import { OrgRole } from '@grafana/data';
import { BrowserContext, expect } from '@playwright/test';
import { BASE_URL } from './constants';

const ORG_ID = process.env.ORG_ID || 1;

export const createGrafanaUserWithRole = async (
  browserContext: BrowserContext,
  login: string,
  password: string,
  role: OrgRole
): Promise<void> => {
  let createUserResponse;
  let didCreateUser = true;

  try {
    createUserResponse = await browserContext.request.post(`${BASE_URL}/api/admin/users`, {
      data: {
        name: login,
        login,
        password,
      },
    });

    expect(createUserResponse.ok()).toBeTruthy();
  } catch (ex) {
    didCreateUser = false;
    expect(true).toBe(false); // CI debug attempt
  }

  if (!didCreateUser || !createUserResponse) return; // skip updating role if user already exists
  if (role === OrgRole.Viewer) return; // viewer by default

  try {
    const updateUserRoleResponse = await updateUserRole(browserContext, createUserResponse.data.id, role);
    expect(updateUserRoleResponse.ok()).toBeTruthy();
  } catch (ex) {
    expect(false).toBe(true);
  }
};

export const updateUserRole = async (browserContext: BrowserContext, userId: string, role: string) => {
  return browserContext.request.patch(`${BASE_URL}/api/orgs/${ORG_ID}/users/${userId}`, {
    data: {
      role,
    },
  });
};
