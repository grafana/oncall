import React from 'react';

import { render } from '@testing-library/react';

import NotificationPoliciesSelect from './NotificationPoliciesSelect';

describe('NotificationPoliciesSelect', () => {
  test('it renders properly', () => {
    const component = render(<NotificationPoliciesSelect important={false} onChange={() => {}} />);
    expect(component.container).toMatchSnapshot();
  });

  test('disabled state', async () => {
    const component = render(<NotificationPoliciesSelect disabled important={false} onChange={() => {}} />);
    expect(component.container).toMatchSnapshot();
  });
});
