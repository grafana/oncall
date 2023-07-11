declare module 'phone' {
  // export iso3166_data: any;

  const a: { [key: string]: any };
  export = a;
}

declare module 'js-cookie';

declare module '*.css';
declare module '*.jpg';
declare module '*.png';
declare module '*.svg';

declare module '*.scss' {
  const content: Record<string, string>;
  export default content;
}

declare module 'grafana/app/core/core' {
  import { OrgRole } from '@grafana/data';

  // https://github.com/grafana/grafana/blob/main/public/app/core/services/context_srv.ts#L59
  export const contextSrv: {
    user: {
      orgRole: OrgRole | '';
      permissions?: Record<string, boolean>;
    };

    hasAccess(action: string, fallBack: boolean): boolean;
    accessControlEnabled(): boolean;
  };
}

// eslint-disable-next-line no-unused-vars
declare namespace Intl {
  /**
   * TODO: can remove this when we upgrade typescript to >= 5.1.3
   * https://github.com/microsoft/TypeScript/issues/49231
   */
  type Key = 'calendar' | 'collation' | 'currency' | 'numberingSystem' | 'timeZone' | 'unit';

  export function supportedValuesOf(input: Key): string[];
}
