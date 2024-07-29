import { AppRootProps as BaseAppRootProps, AppPluginMeta, PluginConfigPageProps, BootData } from '@grafana/data';
import { getPluginId } from 'utils/consts';

export type OnCallPluginMetaJSONData = {
  stackId: number;
  orgId: number;
  onCallApiUrl: string;
  insightsDatasource?: string;
  license: string;
};

export type OnCallPluginMetaSecureJSONData = {
  grafanaToken: string;
  onCallApiToken: string;
};

export type AppRootProps = BaseAppRootProps<OnCallPluginMetaJSONData>;

// NOTE: it is possible that plugin.meta.jsonData is null (ex. on first-ever setup)
// the typing on AppPluginMeta does not seem correct atm..
export type OnCallAppPluginMeta = AppPluginMeta<null | OnCallPluginMetaJSONData>;
export type OnCallPluginConfigPageProps = PluginConfigPageProps<OnCallAppPluginMeta>;

// Extension points that other plugins can use to hook into the OnCall app.
export const OnCallPluginExtensionPoints = {
  AlertGroupAction: `plugins/${getPluginId()}/alert-group/action`,
} as const;
export type OnCallPluginExtensionPoints =
  (typeof OnCallPluginExtensionPoints)[keyof typeof OnCallPluginExtensionPoints];

declare global {
  export interface Window {
    // https://github.com/grafana/grafana/blob/78bef7a26a799209b5307d6bde8e25fcb4fbde7d/public/views/index-template.html#L251-L258
    grafanaBootData?: BootData;
    RECAPTCHA_SITE_KEY: string;
    grecaptcha: any;
    dataLayer: any;
    mixpanel: any;
  }
}
