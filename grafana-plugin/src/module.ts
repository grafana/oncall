import { ComponentClass } from 'react';

import { AppPlugin, PluginExtensionPoints } from '@grafana/data';

import { MobileAppConnectionWrapper } from 'containers/MobileAppConnection/MobileAppConnection';
import { PluginConfigPage } from 'containers/PluginConfigPage/PluginConfigPage';
import { GrafanaPluginRootPage } from 'plugin/GrafanaPluginRootPage';
import { IRM_TAB } from 'utils/consts';
import { isCurrentGrafanaVersionEqualOrGreaterThan } from 'utils/utils';

import { OnCallPluginConfigPageProps, OnCallPluginMetaJSONData } from './types';

const plugin = new AppPlugin<OnCallPluginMetaJSONData>().setRootPage(GrafanaPluginRootPage).addConfigPage({
  title: 'Configuration',
  icon: 'cog',
  body: PluginConfigPage as unknown as ComponentClass<OnCallPluginConfigPageProps, unknown>,
  id: 'configuration',
});

if (isUseProfileExtensionPointEnabled()) {
  const extensionPointId = PluginExtensionPoints.UserProfileTab;

  if (plugin.addComponent) {
    // v11
    plugin.addComponent({
      title: IRM_TAB,
      description: 'IRM settings',
      component: MobileAppConnectionWrapper,
      targets: [extensionPointId],
    });
  } else {
    // v10
    plugin.configureExtensionComponent({
      component: MobileAppConnectionWrapper,
      title: IRM_TAB,
      description: 'IRM settings',
      extensionPointId: extensionPointId,
    });
  }
}

function isUseProfileExtensionPointEnabled(): boolean {
  return (
    isCurrentGrafanaVersionEqualOrGreaterThan({ minMajor: 10, minMinor: 3 }) &&
    'configureExtensionComponent' in plugin &&
    PluginExtensionPoints != null &&
    'UserProfileTab' in PluginExtensionPoints
  );
}

export { plugin };
