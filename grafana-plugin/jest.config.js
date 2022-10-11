module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',

  moduleDirectories: ['node_modules', 'src'],
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json'],

  globals: {
    'ts-jest': {
      isolatedModules: true,
      babelConfig: true
    },
  },

  transform: {
    '^.+\\.js?$': require.resolve('babel-jest'),
    '^.+\\.jsx?$': require.resolve('babel-jest'),
    '^.+\\.ts?$': require.resolve('ts-jest'),
    '^.+\\.tsx?$': require.resolve('ts-jest'),
  },

  moduleNameMapper: {
    "grafana/app/(.*)": '<rootDir>/src/jest/grafanaMock.ts',
    "jest/outgoingWebhooksStub": '<rootDir>/src/jest/outgoingWebhooksStub.ts',
    "^jest$": '<rootDir>/src/jest',
    '^.+\\.(css|scss)$': '<rootDir>/src/jest/styleMock.ts',
    "^lodash-es$": "lodash",
  }
};
