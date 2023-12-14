import { ComponentClass } from 'react';

import { AppPlugin } from '@grafana/data';
import { PluginExtensionPoints } from '@grafana/data';

import MobileAppConnection from 'containers/MobileAppConnection/MobileAppConnection';
import PluginConfigPage from 'containers/PluginConfigPage/PluginConfigPage';
import { GrafanaPluginRootPage } from 'plugin/GrafanaPluginRootPage';
import { getGrafanaVersion } from 'plugin/GrafanaPluginRootPage.helpers';

import { OnCallPluginConfigPageProps, OnCallPluginMetaJSONData } from './types';

const plugin = new AppPlugin<OnCallPluginMetaJSONData>().setRootPage(GrafanaPluginRootPage).addConfigPage({
  title: 'Configuration',
  icon: 'cog',
  body: PluginConfigPage as unknown as ComponentClass<OnCallPluginConfigPageProps, unknown>,
  id: 'configuration',
});

if (isUseProfileExtensionPointEnabled()) {
  // TODO Change this to use the PluginExtensionPoints enum once that is available in @grafana/data (>10.2.2)
  const extensionPointId = 'grafana/user/profile/tab';

  plugin.configureExtensionComponent({
    title: 'IRM',
    description: 'IRM settings',
    extensionPointId,
    /**
     * typing MobileAppConnection as any until 10.2.0 is released
     * https://github.com/grafana/grafana/pull/75019#issuecomment-1724997540
     */
    component: MobileAppConnection as any,
  });
}

function isUseProfileExtensionPointEnabled(): boolean {
  const { major, minor } = getGrafanaVersion();
  const isRequiredGrafanaVersion = major > 10 || (major === 10 && minor >= 3);

  return (
    isRequiredGrafanaVersion &&
    'configureExtensionComponent' in plugin &&
    PluginExtensionPoints != null &&
    'UserProfileTab' in PluginExtensionPoints
  );
}

export { plugin };
