import 'jest/matchMedia.ts';
// import React from 'react';

// import { describe, expect, test } from '@jest/globals';
// import { render, screen } from '@testing-library/react';
// import '@testing-library/jest-dom/extend-expect';

// import ChatOpsPage from './ChatOps';

describe('ChatOps', () => {
  beforeAll(() => {
    console.warn = () => {};
    console.error = () => {};
  });

  jest.mock('@grafana/runtime', () => ({
    config: {
      featureToggles: {
        slack: false,
        telegram: false,
      },
    },
  }));

  //   function getProps(store: jest.Mock = jest.fn()) {
  //     return {
  //       store,
  //     };
  //   }

  // test('It renders alert if chatops features are not enabled', async () => {
  //   render(<ChatOpsPage {...getProps(onClickMock)} />);

  //   expect(screen.getByText('test')).toBe(null);
  // });
});
