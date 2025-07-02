import { ComponentClass } from 'react';

import { AppPlugin, PluginExtensionPoints } from '@grafana/data';
import { getIsIrmPluginPresent, IRM_TAB } from 'helpers/consts';
import { isCurrentGrafanaVersionEqualOrGreaterThan } from 'helpers/helpers';

import { MobileAppConnectionWrapper } from 'containers/MobileAppConnection/MobileAppConnection';
import { PluginConfigPage } from 'containers/PluginConfigPage/PluginConfigPage';
import { GrafanaPluginRootPage } from 'plugin/GrafanaPluginRootPage';

import { OnCallPluginConfigPageProps, OnCallPluginMetaJSONData } from './app-types';

const plugin = new AppPlugin<OnCallPluginMetaJSONData>().setRootPage(GrafanaPluginRootPage).addConfigPage({
  title: 'Configuration',
  icon: 'cog',
  body: PluginConfigPage as unknown as ComponentClass<OnCallPluginConfigPageProps, unknown>,
  id: 'configuration',
});

if (isUseProfileExtensionPointEnabled()) {
  const extensionPointId = PluginExtensionPoints.UserProfileTab;

  if (plugin.addComponent) {
    // v11+ (including v12)
    plugin.addComponent({
      title: IRM_TAB,
      description: 'IRM settings',
      component: MobileAppConnectionWrapper,
      targets: [extensionPointId],
    });
  } else if ('configureExtensionComponent' in plugin) {
    // v10 only (configureExtensionComponent removed in v12)
    // eslint-disable-next-line
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
    PluginExtensionPoints != null &&
    'UserProfileTab' in PluginExtensionPoints &&
    !getIsIrmPluginPresent() &&
    !!(plugin.addComponent || 'configureExtensionComponent' in plugin)
  );
}

export { plugin };
