import React from 'react';

import { render } from '@testing-library/react';
import { Provider } from 'mobx-react';

import AddRespondersPopup from './AddRespondersPopup';

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
    const mockStoreValue = {
      directPagingStore: {
        selectedTeamResponder: null,
      },
      grafanaTeamStore: {
        getSearchResult: jest.fn().mockReturnValue(teams),
      },
      userStore: {
        getSearchResult: jest.fn().mockReturnValue({ results: [] }),
      },
    };

    const component = render(
      <Provider store={mockStoreValue}>
        <AddRespondersPopup
          mode="create"
          visible={true}
          setVisible={jest.fn()}
          setCurrentlyConsideredUser={jest.fn()}
          setShowUserConfirmationModal={jest.fn()}
        />
      </Provider>
    );

    expect(component.container).toMatchSnapshot();
  });

  test('if a team is selected it shows an info alert', () => {
    const mockStoreValue = {
      directPagingStore: {
        selectedTeamResponder: teams[0],
        selectedUserResponders: [],
      },
      grafanaTeamStore: {
        getSearchResult: jest.fn().mockReturnValue(teams),
      },
      userStore: {
        getSearchResult: jest.fn().mockReturnValue({ results: [] }),
      },
    };

    const component = render(
      <Provider store={mockStoreValue}>
        <AddRespondersPopup
          mode="create"
          visible={true}
          setVisible={jest.fn()}
          setCurrentlyConsideredUser={jest.fn()}
          setShowUserConfirmationModal={jest.fn()}
        />
      </Provider>
    );

    expect(component.container).toMatchSnapshot();
  });
});
