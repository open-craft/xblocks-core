/* eslint-env node */
/**
 * PROTOTYPE ONLY (throwaway branch `prototype/problem-paragon-roundtrip`).
 *
 * Separate webpack config for the React + Paragon problem renderer. It is kept
 * out of webpack.config.js on purpose: that config's string-replace loader
 * rewrites legacy RequireJS/jQuery modules and must not touch React sources.
 */
const path = require('path');

module.exports = {
  context: __dirname,
  entry: {
    ProblemReactDisplay: ['./static/js/react/index.jsx'],
  },
  output: {
    filename: '[name].js',
    path: path.resolve(__dirname, '../public/js'),
  },
  resolve: {
    extensions: ['.js', '.jsx', '.json'],
  },
  module: {
    rules: [
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: [
              ['@babel/preset-env', { targets: 'defaults' }],
              ['@babel/preset-react', { runtime: 'automatic' }],
            ],
          },
        },
      },
      {
        test: /\.css$/,
        use: ['style-loader', { loader: 'css-loader', options: { url: false } }],
      },
      {
        // Paragon's dist/utils/breakpoints.js imports its breakpoint map from
        // this SCSS module; compile only that module (no theme SCSS pipeline).
        test: /\.module\.scss$/,
        use: [
          { loader: 'css-loader', options: { modules: true, url: false } },
          'sass-loader',
        ],
      },
    ],
  },
  optimization: {
    minimize: false,
  },
  mode: 'development',
  devtool: 'source-map',
};
