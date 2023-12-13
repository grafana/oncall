import { ComponentClass } from 'react';

import { AppPlugin, PluginExtensionPoints } from '@grafana/data';
import IRMSettings from 'irmSettings';

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
  'configureExtensionComponent' in plugin &&
  PluginExtensionPoints != null &&
  'UserProfileTab' in PluginExtensionPoints
) {
  const IRMSettingsTabTitle = 'IRM';
  // const OnCallSettingsTabTitle = 'OnCall';

  // TODO: change this to use the PluginExtensionPoints enum once we update the @grafana/data package
  const extensionPointId = 'grafana/user/profile/tab';

  plugin.configureExtensionComponent({
    title: IRMSettingsTabTitle,
    description: 'hello world',
    extensionPointId,
    /**
     * typing IRMSettings as any until 10.2.0 is released
     * https://github.com/grafana/grafana/pull/75019#issuecomment-1724997540
     */
    component: IRMSettings as any,
  });

  console.log('passed');

  // plugin.configureExtensionComponent({
  //   title: IRMSettingsTabTitle,
  //   description: 'hello world123',
  //   extensionPointId,
  //   /**
  //    * typing IRMSettings as any until 10.2.0 is released
  //    * https://github.com/grafana/grafana/pull/75019#issuecomment-1724997540
  //    */
  //   component: SomeMoreIRMSettings as any,
  // });

  // plugin.configureExtensionComponent({
  //   title: OnCallSettingsTabTitle,
  //   // TODO: what is the description needed for? I don't think we actually need it but it is a required attribute
  //   description: 'hello world',
  //   extensionPointId,
  //   /**
  //    * typing MobileAppConnection as any until 10.2.0 is released
  //    * https://github.com/grafana/grafana/pull/75019#issuecomment-1724997540
  //    */
  //   component: MobileAppConnection as any,
  // });
}

export { plugin };
