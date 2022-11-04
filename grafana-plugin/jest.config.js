const esModules = ['react-colorful', 'uuid', 'ol'].join('|');

module.exports = {
  testEnvironment: 'jsdom',

  moduleDirectories: ['node_modules', 'src'],
  moduleFileExtensions: ['ts', 'tsx', 'js'],

  transformIgnorePatterns: [`/node_modules/(?!${esModules})`],

  moduleNameMapper: {
    'grafana/app/(.*)': '<rootDir>/src/jest/grafanaMock.ts',
    'jest/matchMedia': '<rootDir>/src/jest/matchMedia.ts',
    'jest/outgoingWebhooksStub': '<rootDir>/src/jest/outgoingWebhooksStub.ts',
    '^jest$': '<rootDir>/src/jest',
    '^.+\\.(css|scss)$': '<rootDir>/src/jest/styleMock.ts',
    '^lodash-es$': 'lodash',
  },
};