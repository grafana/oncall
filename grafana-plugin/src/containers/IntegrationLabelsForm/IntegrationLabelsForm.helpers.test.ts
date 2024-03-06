import { getIsTooManyLabelsWarningVisible } from './IntegrationLabelsForm.helpers';

describe('getIsTooManyLabelsWarningVisible()', () => {
  const CUSTOM_LABEL = {
    key: { id: 'c', name: 'c', prescribed: false },
    value: { id: 'c', name: 'c', prescribed: false },
  };

  it('should return false if limit is not exceeded', () => {
    expect(
      getIsTooManyLabelsWarningVisible(
        {
          inheritable: undefined,
          custom: undefined,
          template: null,
        },
        3
      )
    ).toBe(false);
    expect(
      getIsTooManyLabelsWarningVisible(
        {
          inheritable: { a: true, b: false },
          custom: [CUSTOM_LABEL, CUSTOM_LABEL],
          template: null,
        },
        3
      )
    ).toBe(false);
  });

  it('should return true if limit is exceeded', () => {
    expect(
      getIsTooManyLabelsWarningVisible(
        {
          inheritable: { a: true, b: true },
          custom: [CUSTOM_LABEL, CUSTOM_LABEL],
          template: null,
        },
        3
      )
    ).toBe(true);
  });
});
