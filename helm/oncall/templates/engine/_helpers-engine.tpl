{{/*
Maximum of 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
*/}}
{{- define "oncall.engine.name" -}}
{{ include "oncall.name" . | trunc 55 }}-engine
{{- end }}

{{- define "oncall.engine.fullname" -}}
{{ include "oncall.fullname" . | trunc 55 }}-engine
{{- end }}

{{/*
Engine common labels
*/}}
{{- define "oncall.engine.labels" -}}
{{ include "oncall.labels" . }}
app.kubernetes.io/component: engine
{{- end }}

{{/*
Engien selector labels
*/}}
{{- define "oncall.engine.selectorLabels" -}}
{{ include "oncall.selectorLabels" . }}
app.kubernetes.io/component: engine
{{- end }}
