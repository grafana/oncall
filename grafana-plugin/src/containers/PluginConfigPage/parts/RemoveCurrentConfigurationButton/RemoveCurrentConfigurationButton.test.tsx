import React from 'react';

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import RemoveCurrentConfigurationButton from '.';

describe('RemoveCurrentConfigurationButton', () => {
  test('It renders properly when enabled', () => {
    const component = render(<RemoveCurrentConfigurationButton onClick={() => {}} disabled={false} />);
    expect(component.baseElement).toMatchSnapshot();
  });

  test('It renders properly when disabled', () => {
    const component = render(<RemoveCurrentConfigurationButton onClick={() => {}} disabled />);
    expect(component.baseElement).toMatchSnapshot();
  });

  test('It calls the onClick handler when clicked', async () => {
    const mockedOnClick = jest.fn();

    render(<RemoveCurrentConfigurationButton onClick={mockedOnClick} disabled={false} />);

    // click the button, which opens the modal
    await userEvent.click(screen.getByRole('button'));
    // click the confirm button within the modal, which actually triggers the callback
    await userEvent.click(screen.getByText('Remove'));

    expect(mockedOnClick).toHaveBeenCalledWith();
    expect(mockedOnClick).toHaveBeenCalledTimes(1);
  });
});
