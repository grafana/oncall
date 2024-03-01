const rulesDirPlugin = require('eslint-plugin-rulesdir');
rulesDirPlugin.RULES_DIR = 'tools/eslint-rules';

module.exports = {
  extends: ['./.config/.eslintrc'],
  plugins: ['rulesdir', 'import', 'unused-imports'],
  settings: {
    'import/internal-regex':
      '^assets|^components|^containers|^contexts|^icons|^models|^network|^pages|^services|^state|^utils|^plugin',
  },
  rules: {
    eqeqeq: 'warn',
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
    'no-console': ['warn', { allow: ['warn', 'error'] }],
    'no-unused-vars': 'off',
    'unused-imports/no-unused-imports': ['warn'],
    'unused-imports/no-unused-vars': [
      'warn',
      {
        vars: 'all',
        args: 'after-used',
        argsIgnorePattern: '^_',
        destructuredArrayIgnorePattern: '^_',
        ignoreRestSiblings: true,
      },
    ],
    'no-duplicate-imports': 'error',
    'no-restricted-imports': 'warn',
    // https://eslint.org/docs/latest/rules/no-redeclare#handled_by_typescript
    'no-redeclare': 0,
    'react/display-name': 'warn',
    /**
     * It appears as though the react/prop-types rule has a bug in it
     * when your props extend an interface
     * https://github.com/jsx-eslint/eslint-plugin-react/issues/3325
     */
    'react/prop-types': 'off',
    'react/no-unused-prop-types': 'off',
    'react/jsx-key': 'warn',
    'react/jsx-no-target-blank': 'warn',
    'react/no-unescaped-entities': 'off',
    /**
     * TODO: react-hooks/exhaustive-deps is temporarily disabled
     * this will be turned back on, and the warnings fixed, in a forthcoming PR
     */
    'react-hooks/exhaustive-deps': 'off',
    'rulesdir/no-relative-import-paths': ['error', { allowSameFolder: true }],
    '@typescript-eslint/explicit-member-accessibility': 'off',
  },
};
