import React, { FC, useCallback } from 'react';

import { CodeEditor, CodeEditorSuggestionItemKind, LoadingPlaceholder } from '@grafana/ui';

import { getPaths } from 'utils';

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
  language?: MONACO_LANGUAGE;
  onChange?: (value: string) => void;
  loading?: boolean;
  monacoOptions?: any;
  suggestionPrefix?: string;
}

export enum MONACO_LANGUAGE {
  json = 'json',
  jinja2 = 'jinja2',
}

const PREDEFINED_TERMS = [
  'grafana_oncall_link',
  'integration_name',
  'grafana_oncall_incident_id',
  'source_link',
  'tojson_pretty',
];

const MonacoEditor: FC<MonacoEditorProps> = (props) => {
  const {
    value,
    onChange,
    disabled,
    data,
    language = MONACO_LANGUAGE.jinja2,
    useAutoCompleteList = true,
    focus = true,
    height = '130px',
    monacoOptions,
    showLineNumbers = true,
    loading = false,
    suggestionPrefix = 'payload.',
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

    if (language === MONACO_LANGUAGE.jinja2) {
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
    />
  );
};

export default MonacoEditor;
