import { Configuration, DefinePlugin, EnvironmentPlugin } from 'webpack';
import LiveReloadPlugin from 'webpack-livereload-plugin';
import { mergeWithRules, CustomizeRule } from 'webpack-merge';

import grafanaConfig from './.config/webpack/webpack.config';

const dotenv = require('dotenv');

const config = async (env): Promise<Configuration> => {
  const baseConfig = await grafanaConfig(env);
  const customConfig = {
    module: {
      rules: [
        {
          test: /\.[tj]sx?$/,
          use: {
            options: {
              jsc: {
                parser: {
                  decorators: true,
                },
              },
            },
          },
        },
        {
          test: /\.s[ac]ss$/,
          use: [
            'style-loader',
            {
              loader: 'css-loader',
              options: {
                modules: {
                  auto: true,
                  localIdentName: env.development ? '[path][name]__[local]' : '[name]__[hash:base64]',
                },
              },
            },
            'sass-loader',
          ],
        },
        {
          test: /\.css$/,
          use: [
            'style-loader',
            {
              loader: 'css-loader',
              options: {
                modules: {
                  auto: true,
                  localIdentName: env.development ? '[path][name]__[local]' : '[name]__[hash:base64]',
                },
              },
            },
          ],
        },
      ],
    },
    watchOptions: {
      ignored: ['**/node_modules/', '**/dist'],
    },
    plugins: [
      ...(baseConfig.plugins?.filter((plugin) => !(plugin instanceof LiveReloadPlugin)) || []),
      ...(env.development ? [new LiveReloadPlugin({ appendScriptTag: true, useSourceHash: true })] : []),
      new EnvironmentPlugin({
        ONCALL_API_URL: null,
      }),
      new DefinePlugin({
        'process.env': JSON.stringify(dotenv.config().parsed),
      }),
    ],
  };

  return mergeWithRules({
    module: {
      rules: {
        test: CustomizeRule.Match,
        use: CustomizeRule.Merge,
      },
    },
    watchOptions: {
      use: CustomizeRule.Merge,
    },
    plugins: CustomizeRule.Replace,
  })(baseConfig, customConfig);
};

export default config;
