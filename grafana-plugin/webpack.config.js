const webpack = require('webpack');
const path = require('path');
const dotenv = require('dotenv');

const CircularDependencyPlugin = require('circular-dependency-plugin');

const MONACO_DIR = path.resolve(__dirname, './node_modules/monaco-editor');

Object.defineProperty(RegExp.prototype, 'toJSON', {
  value: RegExp.prototype.toString,
});

dotenv.config({ path: path.resolve(__dirname, '.env') });

module.exports.getWebpackConfig = (config, options) => {
  const cssLoader = config.module.rules.find((rule) => rule.test.toString() === '/\\.css$/');

  cssLoader.exclude.push(/\.module\.css$/, MONACO_DIR);

  const grafanaRules = config.module.rules.filter((a) => a.test.toString() !== /\.s[ac]ss$/.toString());

  const newConfig = {
    ...config,
    module: {
      ...config.module,
      rules: [
        ...grafanaRules,

        {
          test: /\.(ts|tsx)$/,
          exclude: /node_modules/,
          use: [
            {
              loader: 'babel-loader',
              options: {
                cacheDirectory: true,
                cacheCompression: false,
                presets: [
                  [
                    '@babel/preset-env',
                    {
                      modules: false,
                    },
                  ],
                  [
                    '@babel/preset-typescript',
                    {
                      allowNamespaces: true,
                      allowDeclareFields: true,
                    },
                  ],
                  ['@babel/preset-react'],
                ],
                plugins: [
                  [
                    '@babel/plugin-transform-typescript',
                    {
                      allowNamespaces: true,
                      allowDeclareFields: true,
                    },
                  ],
                  '@babel/plugin-proposal-class-properties',
                  [
                    '@babel/plugin-proposal-object-rest-spread',
                    {
                      loose: true,
                    },
                  ],
                  [
                    '@babel/plugin-proposal-decorators',
                    {
                      legacy: true,
                    },
                  ],
                  '@babel/plugin-transform-react-constant-elements',
                  '@babel/plugin-proposal-nullish-coalescing-operator',
                  '@babel/plugin-proposal-optional-chaining',
                  '@babel/plugin-syntax-dynamic-import',
                ],
              },
            },
            'ts-loader',
          ],
        },

        {
          test: /\.module\.css$/,
          exclude: /node_modules/,
          use: [
            'style-loader',
            {
              loader: 'css-loader',
              options: {
                importLoaders: 1,
                sourceMap: true,
                modules: {
                  localIdentName: options.production ? '[name]__[hash:base64]' : '[path][name]__[local]',
                },
              },
            },
          ],
        },

        {
          test: /\.module\.scss$/i,
          exclude: /node_modules/,
          use: [
            'style-loader',
            {
              loader: 'css-loader',
              options: {
                importLoaders: 1,
                sourceMap: true,
                modules: {
                  localIdentName: options.production ? '[name]__[hash:base64]' : '[path][name]__[local]',
                },
              },
            },
            'postcss-loader',
            'sass-loader',
          ],
        },
      ],
    },

    plugins: [
      ...config.plugins,
      new CircularDependencyPlugin({
        // exclude detection of files based on a RegExp
        exclude: /node_modules/,
        // include specific files based on a RegExp
        // add errors to webpack instead of warnings
        failOnError: true,
        // allow import cycles that include an asyncronous import,
        // e.g. via import(/* webpackMode: "weak" */ './file.js')
        allowAsyncCycles: false,
        // set the current working directory for displaying module paths
        cwd: process.cwd(),
      }),

      /**
       * From docs (https://webpack.js.org/plugins/environment-plugin/):
       * Default values of null and undefined behave differently.
       * Use undefined for variables that must be provided during bundling, or null if they are optional.
       */
      new webpack.EnvironmentPlugin({
        ONCALL_API_URL: null,
      }),
      new webpack.DefinePlugin({
        'process.env': JSON.stringify(dotenv.config().parsed),
      }),
    ],

    resolve: {
      ...config.resolve,
      symlinks: false,
      modules: [path.resolve(__dirname, './frontend_enterprise/src'), ...config.resolve.modules],
    },
  };

  return newConfig;
};
