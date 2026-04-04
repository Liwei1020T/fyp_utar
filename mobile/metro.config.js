const path = require('path');
const { getDefaultConfig } = require('expo/metro-config');
const { withUniwindConfig } = require('uniwind/metro');

const exclusionList = require(path.join(
  __dirname,
  'node_modules/metro-config/src/defaults/exclusionList.js',
)).default;

const config = withUniwindConfig(getDefaultConfig(__dirname), {
  cssEntryFile: './global.css',
});

config.resolver.blockList = exclusionList([
  /(^|\/)\._[^/]+$/,
]);

module.exports = config;
