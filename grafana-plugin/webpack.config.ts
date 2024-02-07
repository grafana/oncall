import type { Configuration } from 'webpack';
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
  };

  return mergeWithRules({
    module: {
      rules: {
        test: CustomizeRule.Match,
        use: CustomizeRule.Merge,
      },
    },
  })(baseConfig, customConfig);
};

export default config;
