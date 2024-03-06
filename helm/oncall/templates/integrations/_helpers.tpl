{{/*
Maximum of 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
*/}}
{{- define "oncall.detached_integrations.name" -}}
{{ include "oncall.name" . | trunc 55 }}-integrations
{{- end }}

{{- define "oncall.detached_integrations.fullname" -}}
{{ include "oncall.fullname" . | trunc 55 }}-integrations
{{- end }}

{{/*
Integrations common labels
*/}}
{{- define "oncall.detached_integrations.labels" -}}
{{ include "oncall.labels" . }}
app.kubernetes.io/component: integrations
{{- end }}

{{/*
Integrations selector labels
*/}}
{{- define "oncall.detached_integrations.selectorLabels" -}}
{{ include "oncall.selectorLabels" . }}
app.kubernetes.io/component: integrations
{{- end }}
