/* eslint-env node */
const { merge } = require('webpack-merge');
const devConfig = require('./webpack.react.config.js');
const TerserPlugin = require('terser-webpack-plugin');

module.exports = merge(devConfig, {
  mode: 'production',
  devtool: false,
  optimization: {
    minimize: true,
    minimizer: [
      new TerserPlugin({
        parallel: true,
      }),
    ],
  },
});
