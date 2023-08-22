import { AppRootProps as BaseAppRootProps, AppPluginMeta, CurrentUserDTO, PluginConfigPageProps } from '@grafana/data';

export type OnCallPluginMetaJSONData = {
  stackId: number;
  orgId: number;
  onCallApiUrl: string;
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

declare global {
  export interface Window {
    // https://github.com/grafana/grafana/blob/78bef7a26a799209b5307d6bde8e25fcb4fbde7d/public/views/index-template.html#L251-L258
    grafanaBootData: {
      user: CurrentUserDTO;
      settings: {
        unifiedAlertingEnabled: boolean;
        unifiedAlerting: { minInterval: string };
      };
    };
    RECAPTCHA_SITE_KEY: string;
    grecaptcha: any;
    dataLayer: any;
    mixpanel: any;
  }
}
