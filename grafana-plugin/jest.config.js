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
    "^jest$": '<rootDir>/src/jest',
    '^.+\\.(css|scss)$': '<rootDir>/src/jest/styleMock.ts',
    "^lodash-es$": "lodash",
  }
};
