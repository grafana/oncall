export function mockUseStore() {
  jest.mock('state/useStore', () => ({
    useStore: () => ({
      isUserActionAllowed: jest.fn().mockReturnValue(true),
    }),
  }));
}

export function mockGrafanaLocationSrv() {
  jest.mock('@grafana/runtime', () => ({
    getLocationSrv: jest.fn(),
  }));
}
