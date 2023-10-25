import React from 'react';

import { render } from '@testing-library/react';
import { Provider } from 'mobx-react';

import { DirectPagingContext } from 'state/context/directPaging';

import AddRespondersPopup from './AddRespondersPopup';

const ComponentWithMockedProviders = ({ mockDirectPagingContext, mockStoreValue, children }) => (
  <DirectPagingContext.Provider value={mockDirectPagingContext}>
    <Provider store={mockStoreValue}>{children}</Provider>
  </DirectPagingContext.Provider>
);

describe('AddRespondersPopup', () => {
  const teams = [
    {
      pk: 1,
      avatar_url: 'https://example.com',
      name: 'my test team',
      number_of_users_currently_oncall: 1,
    },
    {
      pk: 2,
      avatar_url: 'https://example.com',
      name: 'my test team 2',
      number_of_users_currently_oncall: 0,
    },
  ];

  test('it renders teams properly', () => {
    const mockContextValue = {
      selectedTeamResponder: null,
      selectedUserResponders: [],
      addUserToSelectedUsers: jest.fn(),
      updateSelectedTeam: jest.fn(),
    };
    const mockStoreValue = {
      grafanaTeamStore: {
        getSearchResult: jest.fn().mockReturnValue(teams),
      },
      userStore: {
        getSearchResult: jest.fn().mockReturnValue({ results: [] }),
      },
    };

    const component = render(
      <ComponentWithMockedProviders mockDirectPagingContext={mockContextValue} mockStoreValue={mockStoreValue}>
        <AddRespondersPopup
          mode="create"
          visible={true}
          setVisible={jest.fn()}
          setCurrentlyConsideredUser={jest.fn()}
          setShowUserConfirmationModal={jest.fn()}
        />
      </ComponentWithMockedProviders>
    );

    expect(component.container).toMatchSnapshot();
  });

  test('if a team is selected it shows an info alert', () => {
    const mockContextValue = {
      selectedTeamResponder: teams[0],
      selectedUserResponders: [],
      addUserToSelectedUsers: jest.fn(),
      updateSelectedTeam: jest.fn(),
    };
    const mockStoreValue = {
      grafanaTeamStore: {
        getSearchResult: jest.fn().mockReturnValue(teams),
      },
      userStore: {
        getSearchResult: jest.fn().mockReturnValue({ results: [] }),
      },
    };

    const component = render(
      <ComponentWithMockedProviders mockDirectPagingContext={mockContextValue} mockStoreValue={mockStoreValue}>
        <AddRespondersPopup
          mode="create"
          visible={true}
          setVisible={jest.fn()}
          setCurrentlyConsideredUser={jest.fn()}
          setShowUserConfirmationModal={jest.fn()}
        />
      </ComponentWithMockedProviders>
    );

    expect(component.container).toMatchSnapshot();
  });

  test('on search it calls the proper store method', () => {
    const mockContextValue = {
      selectedTeamResponder: null,
      selectedUserResponders: [],
      addUserToSelectedUsers: jest.fn(),
      updateSelectedTeam: jest.fn(),
    };
    const mockStoreValue = {
      grafanaTeamStore: {
        getSearchResult: jest.fn().mockReturnValue(teams),
      },
      userStore: {
        getSearchResult: jest.fn().mockReturnValue({ results: [] }),
      },
    };

    const component = render(
      <ComponentWithMockedProviders mockDirectPagingContext={mockContextValue} mockStoreValue={mockStoreValue}>
        <AddRespondersPopup
          mode="create"
          visible={true}
          setVisible={jest.fn()}
          setCurrentlyConsideredUser={jest.fn()}
          setShowUserConfirmationModal={jest.fn()}
        />
      </ComponentWithMockedProviders>
    );

    expect(component.container).toMatchSnapshot();
  });
});
