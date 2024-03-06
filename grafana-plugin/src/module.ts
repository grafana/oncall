import { ComponentClass } from 'react';

import { AppPlugin, PluginExtensionPoints } from '@grafana/data';

import { MobileAppConnectionWrapper } from 'containers/MobileAppConnection/MobileAppConnection';
import { PluginConfigPage } from 'containers/PluginConfigPage/PluginConfigPage';
import { GrafanaPluginRootPage } from 'plugin/GrafanaPluginRootPage';
import { getGrafanaVersion } from 'plugin/GrafanaPluginRootPage.helpers';
import { IRM_TAB } from 'utils/consts';

import { OnCallPluginConfigPageProps, OnCallPluginMetaJSONData } from './types';

const plugin = new AppPlugin<OnCallPluginMetaJSONData>().setRootPage(GrafanaPluginRootPage).addConfigPage({
  title: 'Configuration',
  icon: 'cog',
  body: PluginConfigPage as unknown as ComponentClass<OnCallPluginConfigPageProps, unknown>,
  id: 'configuration',
});

if (isUseProfileExtensionPointEnabled()) {
  const extensionPointId = PluginExtensionPoints.UserProfileTab;

  plugin.configureExtensionComponent({
    title: IRM_TAB,
    description: 'IRM settings',
    extensionPointId,
    /**
     * typing MobileAppConnectionWrapper as any until 10.2.0 is released
     * https://github.com/grafana/grafana/pull/75019#issuecomment-1724997540
     */
    component: MobileAppConnectionWrapper,
  });
}

function isUseProfileExtensionPointEnabled(): boolean {
  const { major, minor } = getGrafanaVersion();
  const isRequiredGrafanaVersion = major > 10 || (major === 10 && minor >= 3); // >= 10.3.0

  return (
    isRequiredGrafanaVersion &&
    'configureExtensionComponent' in plugin &&
    PluginExtensionPoints != null &&
    'UserProfileTab' in PluginExtensionPoints
  );
}

export { plugin };
