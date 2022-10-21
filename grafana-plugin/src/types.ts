import { CurrentUserDTO } from '@grafana/data';

export interface OnCallAppSettings {
  onCallApiUrl?: string;
  grafanaUrl?: string;
  license?: string;
}

declare global {
  export interface Window {
    // https://github.com/grafana/grafana/blob/78bef7a26a799209b5307d6bde8e25fcb4fbde7d/public/views/index-template.html#L251-L258
    grafanaBootData: {
      user: CurrentUserDTO;
    };
    RECAPTCHA_SITE_KEY: string;
    grecaptcha: any;
    dataLayer: any;
    mixpanel: any;
  }
}
