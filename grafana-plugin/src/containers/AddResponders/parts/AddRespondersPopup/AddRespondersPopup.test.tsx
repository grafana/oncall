import React from 'react';

import { render, waitFor } from '@testing-library/react';
import { Provider } from 'mobx-react';

import { UserHelper } from 'models/user/user.helpers';

import { AddRespondersPopup } from './AddRespondersPopup';

describe('AddRespondersPopup', () => {
  const teams = [
    {
      id: 1,
      avatar_url: 'https://example.com',
      name: 'my test team',
      number_of_users_currently_oncall: 1,
    },
    {
      id: 2,
      avatar_url: 'https://example.com',
      name: 'my test team 2',
      number_of_users_currently_oncall: 0,
    },
  ];

  test('it shows a loading message initially', async () => {
    const mockStoreValue = {
      directPagingStore: {
        selectedTeamResponder: null,
      },
      grafanaTeamStore: {
        getSearchResult: jest.fn().mockReturnValue(teams),
        updateItems: jest.fn(),
      },
    };

    UserHelper.search = jest.fn().mockReturnValue({ results: [] });

    await waitFor(() => {
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
});
