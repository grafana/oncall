import React from 'react';

import { render } from '@testing-library/react';
import { Provider } from 'mobx-react';

import AddResponders from './AddResponders';

jest.mock('./parts/AddRespondersPopup/AddRespondersPopup', () => ({
  __esModule: true,
  default: () => <div>AddRespondersPopup</div>,
}));

jest.mock('containers/WithPermissionControl/WithPermissionControlTooltip', () => ({
  WithPermissionControlTooltip: ({ children }) => <div>{children}</div>,
}));

describe('AddResponders', () => {
  const generateRemovePreviouslyPagedUserCallback = jest.fn();

  test.each<'create' | 'update'>(['create', 'update'])('should render properly in %s mode', (mode) => {
    const mockStoreValue = {
      directPagingStore: {
        selectedTeamResponder: null,
        selectedUserResponders: [],
      },
    };

    const component = render(
      <Provider store={mockStoreValue}>
        <AddResponders
          mode={mode}
          generateRemovePreviouslyPagedUserCallback={generateRemovePreviouslyPagedUserCallback}
        />
      </Provider>
    );
    expect(component.container).toMatchSnapshot();
  });

  test.each([true, false])(
    'should properly display the add responders button when hideAddResponderButton is %s',
    (hideAddResponderButton) => {
      const mockStoreValue = {
        directPagingStore: {
          selectedTeamResponder: null,
          selectedUserResponders: [],
        },
      };

      const component = render(
        <Provider store={mockStoreValue}>
          <AddResponders
            mode="create"
            hideAddResponderButton={hideAddResponderButton}
            generateRemovePreviouslyPagedUserCallback={generateRemovePreviouslyPagedUserCallback}
          />
        </Provider>
      );
      expect(component.container).toMatchSnapshot();
    }
  );

  test('should render selected team and users properly', () => {
    const mockStoreValue = {
      directPagingStore: {
        selectedTeamResponder: {
          id: 'asdfasdf',
          avatar_url: 'https://example.com',
          name: 'my test team',
        },
        selectedUserResponders: [
          {
            data: {
              pk: 'mcvnm',
              avatar: 'https://example.com/user123.png',
              username: 'my test user',
            },
          },
          {
            data: {
              pk: 'iuo',
              avatar: 'https://example.com/user456.png',
              username: 'my test user2',
            },
          },
        ],
      },
    };

    const component = render(
      <Provider store={mockStoreValue}>
        <AddResponders
          mode="create"
          existingPagedUsers={[
            {
              pk: 'asdfasdf',
              avatar: 'https://example.com/user9995.png',
              username: 'my test user3',
            } as any,
          ]}
          generateRemovePreviouslyPagedUserCallback={generateRemovePreviouslyPagedUserCallback}
        />
      </Provider>
    );
    expect(component.container).toMatchSnapshot();
  });
});
