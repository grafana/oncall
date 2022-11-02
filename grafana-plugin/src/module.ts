import { ComponentClass } from 'react';

import { AppPlugin, AppPluginMeta, AppRootProps, PluginConfigPageProps } from '@grafana/data';
import { GrafanaPluginRootPage } from 'plugin/GrafanaPluginRootPage';

import { PluginConfigPage } from 'containers/PluginConfigPage/PluginConfigPage';

import { OnCallAppSettings } from './types';

export const plugin = new AppPlugin<OnCallAppSettings>()
  .setRootPage(GrafanaPluginRootPage as unknown as ComponentClass<AppRootProps<OnCallAppSettings>>)
  .addConfigPage({
    title: 'Configuration',
    icon: 'cog',
    body: PluginConfigPage as unknown as ComponentClass<
      PluginConfigPageProps<AppPluginMeta<OnCallAppSettings>>,
      unknown
    >,
    id: 'configuration',
  });
