import React from 'react';

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import DisconnectButton from '.';

describe('DisconnectButton', () => {
  test('it renders properly', () => {
    const component = render(<DisconnectButton onClick={() => {}} />);
    expect(component.container).toMatchSnapshot();
  });

  test('It calls the onClick handler when clicked', async () => {
    const mockedOnClick = jest.fn();

    const user = userEvent.setup();
    render(<DisconnectButton onClick={mockedOnClick} />);

    // click the button, which opens the modal
    await user.click(screen.getByRole('button'));
    // click the confirm button within the modal, which actually triggers the callback
    await user.click(screen.getByText('Remove'));

    expect(mockedOnClick).toHaveBeenCalledWith();
    expect(mockedOnClick).toHaveBeenCalledTimes(1);
  });
});
