import React from 'react';

import { render } from '@testing-library/react';

import { DirectPagingContext } from 'state/context/directPaging';

import AddResponders from './AddResponders';

jest.mock('./parts/AddRespondersPopup', () => ({
  __esModule: true,
  default: () => <div>AddRespondersPopup</div>,
}));

jest.mock('containers/WithPermissionControl/WithPermissionControlTooltip', () => ({
  WithPermissionControlTooltip: ({ children }) => <div>{children}</div>,
}));

describe('AddResponders', () => {
  const generateRemovePreviouslyPagedUserCallback = jest.fn();

  test.each<'create' | 'update'>(['create', 'update'])('should render properly in %s mode', (mode) => {
    const component = render(
      <AddResponders
        mode={mode}
        generateRemovePreviouslyPagedUserCallback={generateRemovePreviouslyPagedUserCallback}
      />
    );
    expect(component.container).toMatchSnapshot();
  });

  test.each([true, false])(
    'should properly display the add responders button when hideAddResponderButton is %s',
    (hideAddResponderButton) => {
      const component = render(
        <AddResponders
          mode="create"
          hideAddResponderButton={hideAddResponderButton}
          generateRemovePreviouslyPagedUserCallback={generateRemovePreviouslyPagedUserCallback}
        />
      );
      expect(component.container).toMatchSnapshot();
    }
  );

  test('should render selected team and users properly', () => {
    const mockContextValue = {
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
      generateRemoveSelectedUserHandler: jest.fn(),
      generateUpdateSelectedUserImportantStatusHandler: jest.fn(),
    } as any;

    const component = render(
      <DirectPagingContext.Provider value={mockContextValue}>
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
      </DirectPagingContext.Provider>
    );
    expect(component.container).toMatchSnapshot();
  });
});
