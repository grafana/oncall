import { ComponentClass } from 'react';

import { AppPlugin, PluginExtensionPoints } from '@grafana/data';

// import MobileAppConnection from 'containers/MobileAppConnection/MobileAppConnection';
import PluginConfigPage from 'containers/PluginConfigPage/PluginConfigPage';
import { GrafanaPluginRootPage } from 'plugin/GrafanaPluginRootPage';

import { OnCallPluginConfigPageProps, OnCallPluginMetaJSONData } from './types';

const plugin = new AppPlugin<OnCallPluginMetaJSONData>().setRootPage(GrafanaPluginRootPage).addConfigPage({
  title: 'Configuration',
  icon: 'cog',
  body: PluginConfigPage as unknown as ComponentClass<OnCallPluginConfigPageProps, unknown>,
  id: 'configuration',
});

if (
  'configureExtensionLink' in plugin &&
  PluginExtensionPoints != null &&
  'ExploreToolbarAction' in PluginExtensionPoints
) {
  console.log('HELLO WORLD!');

  // plugin.configureExtensionComponent({
  //   title: 'OnCall stuff!',
  //   description: 'hello world',
  //   extensionPointId: PluginExtensionPoints.ExploreToolbarAction,
  //   /**
  //    * typing MobileAppConnection as any until 10.2.0 is released
  //    * https://github.com/grafana/grafana/pull/75019#issuecomment-1724997540
  //    */
  //   component: MobileAppConnection as any,
  // });

  // TODO: remove this when finished local testing. Use configureExtensionComponent instead
  plugin.configureExtensionLink({
    title: 'OnCall stuff!',
    description: 'hello world',
    extensionPointId: PluginExtensionPoints.ExploreToolbarAction,
    category: 'OnCall',
    icon: 'fire',
    onClick: async () => {
      console.log('FROM WITHIN ONCALL, HI!');
    },
  });
}

export { plugin };
