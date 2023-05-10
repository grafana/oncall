import React, { FC, useCallback } from 'react';

import { CodeEditor, CodeEditorSuggestionItemKind, LoadingPlaceholder } from '@grafana/ui';

import { getPaths } from 'utils';

import { conf, language as jinja2Language } from './jinja2';

declare const monaco: any;

interface MonacoEditorProps {
  value: string;
  disabled?: boolean;
  height?: string;
  focus?: boolean;
  data: any;
  showLineNumbers?: boolean;
  useAutoCompleteList?: boolean;
  language?: MONACO_LANGUAGE;
  onChange?: (value: string) => void;
  loading?: boolean;
  monacoOptions?: any;
}

export enum MONACO_LANGUAGE {
  json = 'json',
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
    language,
    useAutoCompleteList = true,
    focus = true,
    height = '130px',
    monacoOptions,
    showLineNumbers = true,
    loading = false,
  } = props;

  const autoCompleteList = useCallback(
    () =>
      [...PREDEFINED_TERMS, ...getPaths(data?.payload_example).map((str) => `payload.${str}`)].map((str) => ({
        label: str,
        insertText: str,
        kind: CodeEditorSuggestionItemKind.Field,
      })),
    [data?.payload_example]
  );

  const handleMount = useCallback((editor) => {
    editor.onDidChangeModelContent(() => {
      onChange?.(editor.getValue());
    });

    if (focus) {
      editor.focus();
    }

    const jinja2Lang = monaco.languages.getLanguages().find((l: { id: string }) => l.id === 'jinja2');
    if (!jinja2Lang) {
      monaco.languages.register({ id: 'jinja2' });
      monaco.languages.setLanguageConfiguration('jinja2', conf);
      monaco.languages.setMonarchTokensProvider('jinja2', jinja2Language);
    }
  }, []);

  if (loading) {
    return <LoadingPlaceholder text="Loading..." />;
  }

  const otherProps: any = {};
  if (useAutoCompleteList) {
    otherProps.getSuggestions = { autoCompleteList };
    otherProps.language = language || jinja2Language; // defaults to jinja2
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
      {...otherProps}
    />
  );
};

export default MonacoEditor;
