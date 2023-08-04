const esModules = ['@grafana', 'uplot', 'ol', 'd3', 'react-colorful', 'uuid'].join('|');

module.exports = {
  testEnvironment: 'jsdom',

  moduleDirectories: ['node_modules', 'src'],
  moduleFileExtensions: ['ts', 'tsx', 'js'],

  transformIgnorePatterns: [`/node_modules/(?!${esModules})`],

  moduleNameMapper: {
    'grafana/app/(.*)': '<rootDir>/src/jest/grafanaMock.ts',
    'jest/matchMedia': '<rootDir>/src/jest/matchMedia.ts',
    '^jest$': '<rootDir>/src/jest',
    '^.+\\.(css|scss)$': '<rootDir>/src/jest/styleMock.ts',
    '^lodash-es$': 'lodash',
    '^.+\\.svg$': '<rootDir>/src/jest/svgTransform.ts',
    '^.+\\.png$': '<rootDir>/src/jest/grafanaMock.ts',
  },

  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],

  testTimeout: 10000,
  testPathIgnorePatterns: ['/node_modules/', '/e2e-tests/'],
};
