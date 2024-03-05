import React from 'react';

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { UserResponder } from './UserResponder';
import { ApiSchemas } from 'network/oncall-api/api.types';

describe('UserResponder', () => {
  const user = {
    avatar: 'http://avatar.com/',
    username: 'johnsmith',
  } as ApiSchemas['UserIsCurrentlyOnCall'];

  test('it renders data properly', () => {
    const component = render(
      <UserResponder important data={user} onImportantChange={() => {}} handleDelete={() => {}} />
    );
    expect(component.container).toMatchSnapshot();
  });

  test('it calls the delete callback', async () => {
    const handleDelete = jest.fn();

    render(<UserResponder important data={user} onImportantChange={() => {}} handleDelete={handleDelete} />);

    const deleteIcon = await screen.findByTestId('user-responder-delete-icon');
    await userEvent.click(deleteIcon);

    expect(handleDelete).toHaveBeenCalledTimes(1);
  });
});
