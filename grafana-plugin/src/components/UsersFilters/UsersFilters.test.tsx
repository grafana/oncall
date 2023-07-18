import React from 'react';

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import UsersFilters from './UsersFilters';

describe('UsersFilters', () => {
  test('it renders properly', () => {
    const component = render(<UsersFilters searchTerm="asdfasf" onChange={() => {}} />);
    expect(component.container).toMatchSnapshot();
  });

  test('It properly calls onChange', async () => {
    const searchTerm = 'hello';
    const typedTerm = ' world';
    const className = 'potato';
    const mockOnChange = jest.fn();

    render(<UsersFilters searchTerm={searchTerm} className={className} onChange={mockOnChange} />);

    await userEvent.type(screen.getByRole('textbox'), typedTerm);

    await waitFor(() => {
      expect(mockOnChange).toHaveBeenCalledWith(searchTerm + typedTerm);
    });
  });
});
