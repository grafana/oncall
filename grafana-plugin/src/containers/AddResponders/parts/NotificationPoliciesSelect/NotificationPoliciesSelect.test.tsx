import React from 'react';

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import NotificationPoliciesSelect from '.';

describe('NotificationPoliciesSelect', () => {
  const DEFAULT = 'Default';
  const IMPORTANT = 'Important';

  test('it renders properly', () => {
    const component = render(<NotificationPoliciesSelect important={false} onChange={() => {}} />);
    expect(component.container).toMatchSnapshot();
  });

  test('it calls the onChange callback', async () => {
    const onChange = jest.fn();

    render(<NotificationPoliciesSelect important={false} onChange={onChange} />);

    // first open the drop down list
    const select = await screen.findByText(DEFAULT);
    await userEvent.click(select);

    // click the option
    const defaultLabel = await screen.findByText(IMPORTANT);
    await userEvent.click(defaultLabel);

    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange).toHaveBeenCalledWith(
      { description: 'Use "Important notifications" from users personal settings', label: 'Important', value: 1 },
      { action: 'select-option', name: undefined, option: undefined }
    );
  });

  test('disabled state', async () => {
    const component = render(<NotificationPoliciesSelect disabled important={false} onChange={() => {}} />);
    expect(component.container).toMatchSnapshot();
  });
});
