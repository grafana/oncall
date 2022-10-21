import { OrgRole } from '@grafana/data';
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
  test.each([[false], [true]])('it simply returns the value of contextSrv.hasAccess - %s', (hasAccess) => {
    contextSrv.hasAccess = () => hasAccess;
    expect(auth.isUserActionAllowed(auth.UserActions.APIKeysRead)).toEqual(hasAccess);
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
