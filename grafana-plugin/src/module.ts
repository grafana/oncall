import { ComponentClass } from 'react';

import { AppPlugin } from '@grafana/data';

import PluginConfigPage from 'containers/PluginConfigPage/PluginConfigPage';
import { GrafanaPluginRootPage } from 'plugin/GrafanaPluginRootPage';

import { OnCallPluginConfigPageProps, OnCallPluginMetaJSONData } from './types';

export const plugin = new AppPlugin<OnCallPluginMetaJSONData>().setRootPage(GrafanaPluginRootPage).addConfigPage({
  title: 'Configuration',
  icon: 'cog',
  body: PluginConfigPage as unknown as ComponentClass<OnCallPluginConfigPageProps, unknown>,
  id: 'configuration',
});
