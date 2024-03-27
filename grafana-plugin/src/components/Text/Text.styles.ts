import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getTextStyles = (theme: GrafanaTheme2) => {
  return {
    root: css`
      display: inline;

      &:hover .icon-button {
        display: inline-block;
      }
    `,

    text: css`
      &--primary {
        color: ${theme.colors.primary.text};
      }

      &--secondary {
        color: ${theme.colors.secondary.text};
      }

      &--disabled {
        color: ${theme.colors.text.disabled};
      }

      &--warning {
        color: ${theme.colors.warning.text};
      }

      &--link {
        color: ${theme.colors.text.link};
      }

      &--danger {
        color: ${theme.colors.error.text};
      }

      &--success {
        // TODO: Figure this out
        color: var(--green-5);
      }

      &--strong {
        font-weight: bold;
      }

      &--underline {
        text-decoration: underline;
      }

      &--xs {
        font-size: 8px;
      }

      &--small {
        font-size: 12px;
      }

      &--large {
        font-size: 20px;
      }

      &--clickable {
        cursor: pointer;
      }
    `,

    noWrap: css`
      white-space: nowrap;
    `,
    keyboard: css`
      margin: 0 0.2em;
      padding: 0.15em 0.4em 0.1em;
      font-size: 90%;
      background: hsla(0, 0%, 58.8%, 0.06);
      border: solid hsla(0, 0%, 39.2%, 0.2);
      border-width: 1px 1px 2px;
      border-radius: 3px;
    `,
    title: css`
      margin: 0;
    `,
    iconButton: css`
      margin-left: 8px;
      display: none;
    `,

    maxWidth: css`
      text-overflow: ellipsis;
      white-space: nowrap;
      overflow: hidden;
      display: block;
    `,
  };
};
