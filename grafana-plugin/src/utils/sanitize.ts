import dompurify from 'dompurify';

export default function sanitize(str: string): string {
  return dompurify.sanitize(str, {
    USE_PROFILES: { html: true },
    FORBID_TAGS: ['form', 'input'],
    ADD_ATTR: ['target'],
  });
}
