import React from 'react';

import { OrgRole } from '@grafana/data';
import { contextSrv } from 'grafana/app/core/core';
import renderer from 'react-test-renderer';

import Unauthorized from 'components/Unauthorized';

jest.mock('grafana/app/core/core', () => ({
  contextSrv: {
    accessControlEnabled: (): boolean => null,
  },
}));

describe('Unauthorized', () => {
  test.each([true, false])('renders properly - access control enabled: %s', (accessControlEnabled) => {
    contextSrv.accessControlEnabled = () => accessControlEnabled;
    const tree = renderer
      .create(
        <Unauthorized
          requiredUserAction={{
            permission: 'grafana-oncall-app.testing:hi',
            fallbackMinimumRoleRequired: OrgRole.Admin,
          }}
        />
      )
      .toJSON();
    expect(tree).toMatchSnapshot();
  });

  test.each([OrgRole.Admin, OrgRole.Editor, OrgRole.Viewer])(
    'renders properly the grammar for different roles - %s',
    (role) => {
      contextSrv.accessControlEnabled = () => false;
      const tree = renderer
        .create(
          <Unauthorized
            requiredUserAction={{
              permission: 'grafana-oncall-app.testing:hi',
              fallbackMinimumRoleRequired: role,
            }}
          />
        )
        .toJSON();
      expect(tree).toMatchSnapshot();
    }
  );
});
