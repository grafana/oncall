{{/*
Expand the name of the chart.
*/}}
{{- define "oncall.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "oncall.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "oncall.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "oncall.labels" -}}
helm.sh/chart: {{ include "oncall.chart" . }}
{{ include "oncall.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "oncall.selectorLabels" -}}
app.kubernetes.io/name: {{ include "oncall.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "oncall.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "oncall.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/* Generate the fullname of mariadb subchart */}}
{{- define "oncall.mariadb.fullname" -}}
{{- printf "%s-%s" .Release.Name "mariadb" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/* Generate the fullname of postgresql subchart */}}
{{- define "oncall.postgresql.fullname" -}}
{{- printf "%s-%s" .Release.Name "postgresql" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "oncall.grafana.fullname" -}}
{{- printf "%s-%s" .Release.Name "grafana" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/* Generate the fullname of rabbitmq subchart */}}
{{- define "oncall.rabbitmq.fullname" -}}
{{- printf "%s-%s" .Release.Name "rabbitmq" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/* Generate the fullname of redis subchart */}}
{{- define "oncall.redis.fullname" -}}
{{- printf "%s-%s" .Release.Name "redis" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "oncall.volumes" -}}
{{- if .Values.oncall.devMode }}
volumes:
  - name: dev-reloaded-engine
    hostPath:
      path: /engine
{{- end }}
{{- end }}

{{- define "oncall.volumeMounts" -}}
{{- if .Values.oncall.devMode }}
volumeMounts:
  - mountPath: /etc/app
    name: dev-reloaded-engine
{{- end }}
{{- end }}

{{- define "oncall.initContainer" }}
- name: wait-for-db
  image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
  imagePullPolicy: {{ .Values.image.pullPolicy }}
  command: ['sh', '-c', "until (python manage.py migrate --check); do echo Waiting for database migrations; sleep 2; done"]
  securityContext:
  {{ toYaml .Values.init.securityContext | nindent 4 }}
  resources:
  {{ toYaml .Values.init.resources | nindent 4 }}
  env:
    {{- include "snippet.oncall.env" . | nindent 4 }}
    {{- include "snippet.db.env" . | nindent 4 }}
    {{- include "snippet.broker.env" . | nindent 4 }}
    {{- include "oncall.extraEnvs" . | nindent 4 }}
  {{- include "oncall.volumeMounts" . | nindent 2 }}
{{- end }}

{{- define "oncall.extraEnvs" -}}
{{- if .Values.env }}
  {{- if (kindIs "map" .Values.env) }}
    {{- range $key, $value := .Values.env }}
- name: {{ $key }}
  value: {{ $value }}
    {{- end -}}
  {{/* support previous schema */}}
  {{- else }}
{{- toYaml .Values.env }}
  {{- end }}
{{- end }}
{{- end }}
