import * as runtime from '@grafana/runtime';
import { getGrafanaVersion, isCurrentGrafanaVersionEqualOrGreaterThan } from 'helpers/helpers';

jest.mock('@grafana/runtime', () => ({
  config: jest.fn(),
}));

function setGrafanaVersion(version: string) {
  runtime.config.buildInfo = {
    version,
  } as any;
}

describe('getGrafanaVersion', () => {
  it('figures out grafana version from string', () => {
    setGrafanaVersion('10.13.95-9.0.1.1test');

    const { major, minor, patch } = getGrafanaVersion();

    expect(major).toBe(10);
    expect(minor).toBe(13);
    expect(patch).toBe(95);
  });

  it('figures out grafana version for v9', () => {
    setGrafanaVersion('9.04.3105-rctest100');

    const { major, minor, patch } = getGrafanaVersion();

    expect(major).toBe(9);
    expect(minor).toBe(4);
    expect(patch).toBe(3105);
  });

  it('figures out grafana version for 1.0.0', () => {
    setGrafanaVersion('1.0.0-any-asd-value');

    const { major, minor, patch } = getGrafanaVersion();

    expect(major).toBe(1);
    expect(minor).toBe(0);
    expect(patch).toBe(0);
  });
});

describe('isCurrentGrafanaVersionEqualOrGreaterThan()', () => {
  it('returns true if grafana version is equal or greater than specified version', () => {
    setGrafanaVersion('11.0.0');
    expect(isCurrentGrafanaVersionEqualOrGreaterThan({ minMajor: 11, minMinor: 0, minPatch: 0 })).toBe(true);
    expect(isCurrentGrafanaVersionEqualOrGreaterThan({ minMajor: 10, minMinor: 0, minPatch: 1 })).toBe(true);
    expect(isCurrentGrafanaVersionEqualOrGreaterThan({ minMajor: 10, minMinor: 1, minPatch: 0 })).toBe(true);
    expect(isCurrentGrafanaVersionEqualOrGreaterThan({ minMajor: 10, minMinor: 1, minPatch: 1 })).toBe(true);
    expect(isCurrentGrafanaVersionEqualOrGreaterThan({ minMajor: 11, minMinor: 0, minPatch: 1 })).toBe(false);
    expect(isCurrentGrafanaVersionEqualOrGreaterThan({ minMajor: 12, minMinor: 0, minPatch: 0 })).toBe(false);
  });
});
