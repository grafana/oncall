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
