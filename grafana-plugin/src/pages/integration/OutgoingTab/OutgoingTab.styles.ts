import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getStyles = (theme: GrafanaTheme2) => ({
  urlIntegrationBlock: css({
    marginBottom: '32px',
  }),
  urlInput: css({
    height: '25px',
    background: theme.colors.background.canvas,
    '& input': {
      height: '25px',
    },
  }),
  form: css({
    height: '100%',
    paddingBottom: '64px',
  }),
  formFieldsWrapper: css({
    width: '100%',
  }),
  infoIcon: css({
    marginLeft: '10px',
  }),
  monacoEditorWrapper: css({
    display: 'flex',
    width: '100%',
    gap: '6px',
  }),
  switcherFieldWrapper: css({
    display: 'flex',
    gap: '8px',
    alignItems: 'center',
  }),
  switcherLabel: css({
    marginBottom: 0,
  }),
  selectField: css({
    width: '200px',
    marginBottom: 0,
  }),
  hamburgerIcon: css({
    background: theme.colors.secondary.shade,
  }),
  horizontalGroup: css({
    display: 'flex',
    gap: '8px',
  }),
  addEventTriggerBtn: css({
    marginTop: '16px',
  }),
});
