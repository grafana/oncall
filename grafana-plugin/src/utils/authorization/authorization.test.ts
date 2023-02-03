import { OrgRole } from '@grafana/data';
import { config } from '@grafana/runtime';
import { contextSrv } from 'grafana/app/core/core';

import * as auth from './';

jest.mock('grafana/app/core/core', () => ({
  contextSrv: {
    user: {
      orgRole: null,
    },
    hasAccess: (_action, _fallback): boolean => null,
  },
}));

jest.mock('@grafana/runtime', () => ({
  config: {
    featureToggles: {
      accessControlOnCall: true,
    },
  },
}));

describe('userHasMinimumRequiredRole', () => {
  test.each([
    [OrgRole.Admin, OrgRole.Viewer, false],
    [OrgRole.Admin, OrgRole.Editor, false],
    [OrgRole.Admin, OrgRole.Admin, true],
    [OrgRole.Editor, OrgRole.Viewer, false],
    [OrgRole.Editor, OrgRole.Editor, true],
    [OrgRole.Editor, OrgRole.Admin, true],
    [OrgRole.Viewer, OrgRole.Viewer, true],
    [OrgRole.Viewer, OrgRole.Editor, true],
    [OrgRole.Viewer, OrgRole.Admin, true],
  ])('Required role: %s Current role: %s', (requiredRole, mockCurrentRole, expected) => {
    contextSrv.user.orgRole = mockCurrentRole;
    expect(auth.userHasMinimumRequiredRole(requiredRole)).toBe(expected);
  });
});

describe('isUserActionAllowed', () => {
  test('if RBAC is supported by the frontend, it uses the RBAC permission', () => {
    // mocks
    const permission = 'potato';
    contextSrv.user.permissions = {
      [permission]: true,
    };
    config.featureToggles.accessControlOnCall = true;

    // test + assertions
    expect(auth.isUserActionAllowed({ permission, fallbackMinimumRoleRequired: OrgRole.Viewer })).toEqual(true);
  });

  test('if RBAC is not supported by the frontend, it uses the fallback role', () => {
    // mocks
    const permission = 'potato';
    contextSrv.user.orgRole = OrgRole.Editor;
    config.featureToggles.accessControlOnCall = false;

    // test + assertions
    expect(auth.isUserActionAllowed({ permission, fallbackMinimumRoleRequired: OrgRole.Viewer })).toEqual(true);
    expect(auth.isUserActionAllowed({ permission, fallbackMinimumRoleRequired: OrgRole.Admin })).toEqual(false);
  });
});

describe('determineRequiredAuthString', () => {
  const testPerm = auth.UserActions.UserSettingsRead;

  test.each([
    [true, `${testPerm.permission} permission`],
    [false, `${testPerm.fallbackMinimumRoleRequired} role`],
  ])('RBAC enabled: %s', (rbacEnabled, expected) => {
    config.featureToggles.accessControlOnCall = rbacEnabled;

    expect(auth.determineRequiredAuthString(testPerm)).toBe(expected);
  });
});

describe('generateMissingPermissionMessage', () => {
  const testPerm = auth.UserActions.UserSettingsRead;

  test.each([
    [true, `You are missing the ${testPerm.permission} permission`],
    [false, `You are missing the ${testPerm.fallbackMinimumRoleRequired} role`],
  ])('RBAC enabled: %s', (rbacEnabled, expected) => {
    config.featureToggles.accessControlOnCall = rbacEnabled;

    expect(auth.generateMissingPermissionMessage(testPerm)).toBe(expected);
  });
});

describe('generatePermissionString', () => {
  test('it properly builds permission strings with prefixes', () => {
    expect(auth.generatePermissionString(auth.Resource.API_KEYS, auth.Action.READ, true)).toEqual(
      'grafana-oncall-app.api-keys:read'
    );
  });

  test('it properly builds permission strings without prefixes', () => {
    expect(auth.generatePermissionString(auth.Resource.TEAMS, auth.Action.READ, false)).toEqual('teams:read');
  });
});
