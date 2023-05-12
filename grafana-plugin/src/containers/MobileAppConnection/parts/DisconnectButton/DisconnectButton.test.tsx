import React from 'react';

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import DisconnectButton from './DisconnectButton';

describe('DisconnectButton', () => {
  test('it renders properly', () => {
    const component = render(<DisconnectButton onClick={() => {}} />);
    expect(component.container).toMatchSnapshot();
  });

  test('It calls the onClick handler when clicked', async () => {
    const mockedOnClick = jest.fn();

    render(<DisconnectButton onClick={mockedOnClick} />);

    // click the button, which opens the modal
    await userEvent.click(screen.getByRole('button'));
    // click the confirm button within the modal, which actually triggers the callback
    await userEvent.click(screen.getByText('Remove'));

    expect(mockedOnClick).toHaveBeenCalledWith();
    expect(mockedOnClick).toHaveBeenCalledTimes(1);
  });
});
