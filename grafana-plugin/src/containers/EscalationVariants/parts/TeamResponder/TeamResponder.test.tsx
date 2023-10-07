import React from 'react';

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';

import TeamResponder from './';

describe('TeamResponder', () => {
  const team = {
    avatar_url: 'https://example.com',
    name: 'my test team',
  } as GrafanaTeam;

  test('it renders data properly', () => {
    const component = render(
      <TeamResponder important data={team} onImportantChange={() => {}} handleDelete={() => {}} />
    );
    expect(component.container).toMatchSnapshot();
  });

  test('it calls the delete callback', async () => {
    const handleDelete = jest.fn();

    render(<TeamResponder important data={team} onImportantChange={() => {}} handleDelete={handleDelete} />);

    const deleteIcon = await screen.findByTestId('team-responder-delete-icon');
    await userEvent.click(deleteIcon);

    expect(handleDelete).toHaveBeenCalledTimes(1);
  });
});
