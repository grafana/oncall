export function mockUseStore() {
  jest.mock('state/useStore', () => ({
    useStore: () => ({
      isUserActionAllowed: jest.fn().mockReturnValue(true),
    }),
  }));
}
