{{/*
Maximum of 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
*/}}
{{- define "oncall.telegramPolling.fullname" -}}
{{ include "oncall.fullname" . | trunc 45 }}-telegram-polling
{{- end }}

{{/*
Telegram polling common labels
*/}}
{{- define "oncall.telegramPolling.labels" -}}
{{ include "oncall.labels" . }}
app.kubernetes.io/component: telegram-polling
{{- end }}

{{/*
Telegram polling selector labels
*/}}
{{- define "oncall.telegramPolling.selectorLabels" -}}
{{ include "oncall.selectorLabels" . }}
app.kubernetes.io/component: telegram-polling
{{- end }}
