const path = require('path');
const fs = require('fs');
const CopyWebpackPlugin = require('copy-webpack-plugin');

const CircularDependencyPlugin = require('circular-dependency-plugin');
const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;

const MONACO_DIR = path.resolve(__dirname, './node_modules/monaco-editor');

Object.defineProperty(RegExp.prototype, 'toJSON', {
  value: RegExp.prototype.toString,
});

module.exports.getWebpackConfig = (config, options) => {
  const cssLoader = config.module.rules.find((rule) => rule.test.toString() === '/\\.css$/');
  const tsxLoader = config.module.rules.find((rule) => rule.test.toString() === '/\\.tsx?$/');

  cssLoader.exclude.push(/\.module\.css$/, MONACO_DIR);

  const newConfig = {
    ...config,
    module: {
      ...config.module,
      rules: [
        ...config.module.rules,
        {
          test: /\.module\.css$/,
          exclude: /node_modules/,
          //use: ['style-loader', 'css-loader?modules&importLoaders=1&localIdentName=[name]__[local]___[hash:base64:5]!postcss-loader'],
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
      //new BundleAnalyzerPlugin(),
    ],
    resolve: {
      ...config.resolve,
      symlinks: false,
      modules: [path.resolve(__dirname, './frontend_enterprise/src'), ...config.resolve.modules],
    },
  };

  /* fs.writeFile('webpack-conf.json', JSON.stringify(newConfig.resolve, null, 2), function (err) {
    if (err) {
      return console.log(err);
    }
    console.log('config > webpack-conf.json');
  }); */

  return newConfig;
};
