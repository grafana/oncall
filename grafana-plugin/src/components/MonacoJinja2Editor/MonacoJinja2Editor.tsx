import React, { FC, useCallback } from 'react';

import { CodeEditor, CodeEditorSuggestionItemKind, LoadingPlaceholder } from '@grafana/ui';

import { getPaths } from 'utils';

import { conf, language } from './jinja2';

declare const monaco: any;

interface MonacoJinja2EditorProps {
  value: string;
  disabled?: boolean;
  height?: number;
  data: any;
  onChange?: (value: string) => void;
  loading?: boolean;
}

const PREDEFINED_TERMS = [
  'grafana_oncall_link',
  'integration_name',
  'grafana_oncall_incident_id',
  'source_link',
  'tojson_pretty',
];

const MonacoJinja2Editor: FC<MonacoJinja2EditorProps> = (props) => {
  const { value, onChange, disabled, data, height, loading = false } = props;

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

    editor.focus();

    const jinja2Lang = monaco.languages.getLanguages().find((l: { id: string }) => l.id === 'jinja2');
    if (!jinja2Lang) {
      monaco.languages.register({ id: 'jinja2' });
      monaco.languages.setLanguageConfiguration('jinja2', conf);
      monaco.languages.setMonarchTokensProvider('jinja2', language);
    }
  }, []);

  if (loading) {
    return <LoadingPlaceholder text="Loading..." />;
  }

  return (
    <CodeEditor
      showMiniMap={false}
      readOnly={disabled}
      showLineNumbers
      value={value}
      language="jinja2"
      width="100%"
      height={height ? `${height}px` : `130px`}
      onEditorDidMount={handleMount}
      getSuggestions={autoCompleteList}
    />
  );
};

export default MonacoJinja2Editor;
