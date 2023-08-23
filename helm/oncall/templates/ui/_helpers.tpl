{{- define "ui.env" -}}
{{- if .Values.ui.env }}
    {{- range $key, $value := .Values.ui.env }}
- name: {{ $key }}
  value: "{{ $value }}"
    {{- end -}}
{{- end }}
{{- end }}
