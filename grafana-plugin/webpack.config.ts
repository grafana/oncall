import type { Configuration } from 'webpack';
import LiveReloadPlugin from 'webpack-livereload-plugin';
import { mergeWithRules, CustomizeRule } from 'webpack-merge';

import grafanaConfig from './.config/webpack/webpack.config';

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
      ],
    },
    watchOptions: {
      ignored: ['**/node_modules/', '**/dist'],
    },
    plugins: env.development ? [new LiveReloadPlugin({ appendScriptTag: true, useSourceHash: true })] : [],
  };

  return mergeWithRules({
    module: {
      rules: {
        test: CustomizeRule.Match,
        use: CustomizeRule.Merge,
      },
    },
    plugins: CustomizeRule.Replace,
    watchOptions: {
      use: CustomizeRule.Merge,
    },
  })(baseConfig, customConfig);
};

export default config;
