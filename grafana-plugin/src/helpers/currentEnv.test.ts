describe('determineCurrentEnv', () => {
  beforeEach(() => {
    jest.resetModules(); // Clear module cache
  });

  test.each([
    ['cloud', 'grafana-oncall-app-v1.0.0-1234-abc'],
    ['cloud', 'v1.2.3'],
    ['cloud', 'grafana-irm-app-v2.3.4-5678-xyz'],
    ['cloud', 'grafana-oncall-app-v3.4.5-91011-uvw'],
    ['cloud', 'grafana-oncall-app-v3.4.5'],
    ['oss', '1.0.0'],
  ])('should return "%s" if version is "%s"', (expected, version) => {
    jest.mock('../../package.json', () => ({ version }), { virtual: true });
    const { determineCurrentEnv } = require('./currentEnv'); // Re-import after mocking
    expect(determineCurrentEnv()).toBe(expected);
  });

  it('should return "local" if NODE_ENV is "development"', () => {
    process.env.NODE_ENV = 'development';
    jest.mock('../../package.json', () => ({ version: '1.0.0' }), { virtual: true });
    const { determineCurrentEnv } = require('./currentEnv'); // Re-import after mocking
    expect(determineCurrentEnv()).toBe('local');
  });

  it('should return "oss" if NODE_ENV is not "development"', () => {
    process.env.NODE_ENV = 'production';
    jest.mock('../../package.json', () => ({ version: '1.0.0' }), { virtual: true });
    const { determineCurrentEnv } = require('./currentEnv'); // Re-import after mocking
    expect(determineCurrentEnv()).toBe('oss');
  });

  it('should return "cloud" if there is an error accessing process.env.NODE_ENV', () => {
    const originalEnv = process.env;
    delete process.env;

    jest.mock('../../package.json', () => ({ version: '1.0.0' }), { virtual: true });
    const { determineCurrentEnv } = require('./currentEnv'); // Re-import after mocking

    expect(determineCurrentEnv()).toBe('cloud');
    process.env = originalEnv;
  });
});
