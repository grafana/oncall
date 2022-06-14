{{/*
Maximum of 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
*/}}
{{- define "oncall.celery.name" -}}
{{ include "oncall.name" . | trunc 55 }}-celery
{{- end }}

{{- define "oncall.celery.fullname" -}}
{{ include "oncall.fullname" . | trunc 55 }}-celery
{{- end }}

{{/*
Engine common labels
*/}}
{{- define "oncall.celery.labels" -}}
{{ include "oncall.labels" . }}
app.kubernetes.io/component: celery
{{- end }}

{{/*
Engine selector labels
*/}}
{{- define "oncall.celery.selectorLabels" -}}
{{ include "oncall.selectorLabels" . }}
app.kubernetes.io/component: celery
{{- end }}
