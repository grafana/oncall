const rulesDirPlugin = require('eslint-plugin-rulesdir');
rulesDirPlugin.RULES_DIR = 'tools/eslint-rules';

module.exports = {
  extends: ['@grafana/eslint-config'],
  plugins: ['rulesdir', 'import'],
  settings: {
    'import/internal-regex':
      '^assets|^components|^containers|^declare|^icons|^img|^interceptors|^models|^network|^pages|^services|^state|^utils',
  },
  rules: {
    'no-unused-vars': ['warn', { vars: 'all', args: 'after-used', ignoreRestSiblings: false }],
    'react/prop-types': 'warn',
    'react/display-name': 'warn',
    'react/jsx-key': 'warn',
    'react-hooks/exhaustive-deps': 'off',
    'react/no-unescaped-entities': 'warn',
    'react/jsx-no-target-blank': 'warn',
    'react-hooks/exhaustive-deps': 'warn',
    'no-restricted-imports': 'warn',
    eqeqeq: 'warn',
    'no-duplicate-imports': 'error',
    'rulesdir/no-relative-import-paths': ['error', { allowSameFolder: true }],
    'import/order': [
      'error',
      {
        pathGroups: [
          {
            pattern: 'react',
            group: 'external',
            position: 'before',
          },
          {
            pattern: '*.module.css',
            patternOptions: {
              matchBase: true,
            },
            group: 'unknown',
            position: 'after',
          },
        ],
        pathGroupsExcludedImportTypes: ['react'],
        alphabetize: {
          order: 'asc',
        },
        groups: ['external', 'internal', 'parent', 'sibling', 'index', 'unknown'],
        'newlines-between': 'always',
      },
    ],
  },
};
