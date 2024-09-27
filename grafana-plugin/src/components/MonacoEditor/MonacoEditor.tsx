import React, { ComponentProps, FC, useCallback } from 'react';

import { css, cx } from '@emotion/css';
import { CodeEditor, CodeEditorSuggestionItemKind, LoadingPlaceholder } from '@grafana/ui';
import { getPaths } from 'helpers/helpers';

import { conf, language as jinja2Language } from './jinja2';

declare const monaco: any;

interface MonacoEditorProps {
  value: string;
  disabled?: boolean;
  height?: string | number;
  focus?: boolean;
  data: any;
  showLineNumbers?: boolean;
  useAutoCompleteList?: boolean;
  language?: MonacoLanguage;
  onChange?: (value: string) => void;
  loading?: boolean;
  monacoOptions?: any;
  suggestionPrefix?: string;
  containerClassName?: string;
  codeEditorProps?: Partial<ComponentProps<typeof CodeEditor>>;
}

export enum MonacoLanguage {
  json = 'json',
  jinja2 = 'jinja2',
}

const PREDEFINED_TERMS = [
  'grafana_oncall_link',
  'integration_name',
  'grafana_oncall_incident_id',
  'source_link',
  'tojson_pretty',
  'tojson',
];

export const MonacoEditor: FC<MonacoEditorProps> = (props) => {
  const {
    value,
    onChange,
    disabled,
    data,
    language = MonacoLanguage.jinja2,
    useAutoCompleteList = true,
    focus = true,
    height = '130px',
    monacoOptions,
    showLineNumbers = true,
    loading = false,
    suggestionPrefix = 'payload.',
    containerClassName,
    codeEditorProps,
  } = props;

  const autoCompleteList = useCallback(
    () =>
      [...PREDEFINED_TERMS, ...getPaths(data?.payload_example).map((str) => `${suggestionPrefix}${str}`)].map(
        (str) => ({
          label: str,
          insertText: str,
          kind: CodeEditorSuggestionItemKind.Field,
        })
      ),
    [data?.payload_example]
  );

  const handleMount = useCallback((editor) => {
    editor.onDidChangeModelContent(() => {
      onChange?.(editor.getValue());
    });

    if (focus) {
      editor.focus();
    }

    if (language === MonacoLanguage.jinja2) {
      const jinja2Lang = monaco.languages.getLanguages().find((l: { id: string }) => l.id === 'jinja2');
      if (!jinja2Lang) {
        monaco.languages.register({ id: 'jinja2' });
        monaco.languages.setLanguageConfiguration('jinja2', conf);
        monaco.languages.setMonarchTokensProvider('jinja2', jinja2Language);
      }
    }
  }, []);

  if (loading) {
    return <LoadingPlaceholder text="Loading..." />;
  }

  return (
    <CodeEditor
      monacoOptions={monacoOptions}
      showMiniMap={false}
      readOnly={disabled}
      showLineNumbers={showLineNumbers}
      value={value}
      language={language}
      width="100%"
      height={height}
      onEditorDidMount={handleMount}
      getSuggestions={useAutoCompleteList ? autoCompleteList : undefined}
      containerStyles={cx(
        css`
          width: 100%;
          height: 100%;
        `,
        containerClassName
      )}
      {...codeEditorProps}
    />
  );
};
