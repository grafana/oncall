{{- define "snippet.oncall.env" -}}
- name: BASE_URL
  value: {{ .Values.base_url_protocol }}://{{ .Values.base_url }}
- name: SECRET_KEY
  valueFrom:
    secretKeyRef:
      name: {{ include "snippet.oncall.secret.name" . }}
      key: {{ include "snippet.oncall.secret.secretKey" . | quote }}
- name: MIRAGE_SECRET_KEY
  valueFrom:
    secretKeyRef:
      name: {{ include "snippet.oncall.secret.name" . }}
      key: {{ include "snippet.oncall.secret.mirageSecretKey" . | quote }}
- name: MIRAGE_CIPHER_IV
  value: {{ .Values.oncall.mirageCipherIV | default "1234567890abcdef" | quote }}
- name: DJANGO_SETTINGS_MODULE
  value: "settings.helm"
- name: AMIXR_DJANGO_ADMIN_PATH
  value: "admin"
- name: OSS
  value: "True"
{{- include "snippet.oncall.uwsgi" . }}
- name: BROKER_TYPE
  value: {{ .Values.broker.type | default "rabbitmq" }}
- name: GRAFANA_API_URL
  value: {{ include "snippet.grafana.url" . | quote }}
{{- end }}

{{- define "snippet.oncall.secret.name" -}}
{{ if .Values.oncall.secrets.existingSecret -}}
  {{ .Values.oncall.secrets.existingSecret }}
{{- else -}}
  {{ include "oncall.fullname" . }}
{{- end }}
{{- end }}

{{- define "snippet.oncall.secret.secretKey" -}}
{{ if .Values.oncall.secrets.existingSecret -}}
  {{ required "oncall.secrets.secretKey is required if oncall.secret.existingSecret is not empty" .Values.oncall.secrets.secretKey }}
{{- else -}}
  SECRET_KEY
{{- end }}
{{- end }}

{{- define "snippet.oncall.secret.mirageSecretKey" -}}
{{ if .Values.oncall.secrets.existingSecret -}}
  {{ required "oncall.secrets.mirageSecretKey is required if oncall.secret.existingSecret is not empty" .Values.oncall.secrets.mirageSecretKey }}
{{- else -}}
  MIRAGE_SECRET_KEY
{{- end }}
{{- end }}

{{- define "snippet.oncall.uwsgi" -}}
{{- if .Values.uwsgi }}
  {{- range $key, $value := .Values.uwsgi }}
- name: UWSGI_{{ $key | upper | replace "-" "_" }}
  value: {{ $value | quote }}
  {{- end }}
{{- end }}
{{- end }}

{{- define "snippet.oncall.slack.env" -}}
- name: FEATURE_SLACK_INTEGRATION_ENABLED
  value: {{ .Values.oncall.slack.enabled | toString | title | quote }}
{{- if .Values.oncall.slack.enabled }}
- name: SLACK_SLASH_COMMAND_NAME
  value: "/{{ .Values.oncall.slack.commandName | default "oncall" }}"
{{- if .Values.oncall.slack.existingSecret }}
- name: SLACK_CLIENT_OAUTH_ID
  valueFrom:
    secretKeyRef:
      name: {{ .Values.oncall.slack.existingSecret }}
      key: {{ required "oncall.slack.clientIdKey is required if oncall.slack.existingSecret is not empty" .Values.oncall.slack.clientIdKey | quote }}
- name: SLACK_CLIENT_OAUTH_SECRET
  valueFrom:
    secretKeyRef:
      name: {{ .Values.oncall.slack.existingSecret }}
      key: {{ required "oncall.slack.clientSecretKey is required if oncall.slack.existingSecret is not empty" .Values.oncall.slack.clientSecretKey | quote }}
- name: SLACK_SIGNING_SECRET
  valueFrom:
    secretKeyRef:
      name: {{ .Values.oncall.slack.existingSecret }}
      key: {{ required "oncall.slack.signingSecretKey is required if oncall.slack.existingSecret is not empty" .Values.oncall.slack.signingSecretKey | quote }}
{{- else }}
- name: SLACK_CLIENT_OAUTH_ID
  value: {{ .Values.oncall.slack.clientId | default "" | quote }}
- name: SLACK_CLIENT_OAUTH_SECRET
  value: {{ .Values.oncall.slack.clientSecret | default "" | quote }}
- name: SLACK_SIGNING_SECRET
  value: {{ .Values.oncall.slack.signingSecret | default "" | quote }}
{{- end }}
- name: SLACK_INSTALL_RETURN_REDIRECT_HOST
  value: {{ .Values.oncall.slack.redirectHost | default (printf "https://%s" .Values.base_url) | quote }}
{{- end }}
{{- end }}

{{- define "snippet.oncall.telegram.env" -}}
{{- if .Values.telegramPolling.enabled -}}
{{- $_ := set .Values.oncall.telegram "enabled" true -}}
{{- end -}}
- name: FEATURE_TELEGRAM_INTEGRATION_ENABLED
  value: {{ .Values.oncall.telegram.enabled | toString | title | quote }}
{{- if .Values.oncall.telegram.enabled }}
{{- if .Values.telegramPolling.enabled }}
- name: FEATURE_TELEGRAM_LONG_POLLING_ENABLED
  value: {{ .Values.telegramPolling.enabled | toString | title | quote }}
{{- end }}
- name: TELEGRAM_WEBHOOK_HOST
  value: {{ .Values.oncall.telegram.webhookUrl | default (printf "https://%s" .Values.base_url) | quote }}
{{- if .Values.oncall.telegram.existingSecret }}
- name: TELEGRAM_TOKEN
  valueFrom:
    secretKeyRef:
      name: {{ .Values.oncall.telegram.existingSecret }}
      key: {{ required "oncall.telegram.tokenKey is required if oncall.telegram.existingSecret is not empty" .Values.oncall.telegram.tokenKey | quote }}
{{- else }}
- name: TELEGRAM_TOKEN
  value: {{ .Values.oncall.telegram.token | default "" | quote }}
{{- end }}
{{- end }}
{{- end }}

{{- define "snippet.oncall.twilio.env" }}
{{- with .Values.oncall.twilio }}
{{- if .existingSecret }}
- name: TWILIO_ACCOUNT_SID
  valueFrom:
    secretKeyRef:
      name: {{ .existingSecret }}
      key: {{ required "oncall.twilio.accountSid is required if oncall.twilio.existingSecret is not empty" .accountSid | quote }}
{{- if .authTokenKey }}
- name: TWILIO_AUTH_TOKEN
  valueFrom:
    secretKeyRef:
      name: {{ .existingSecret }}
      key: {{ required "oncall.twilio.authTokenKey is required if oncall.twilio.existingSecret is not empty" .authTokenKey | quote }}
{{- end }}
- name: TWILIO_NUMBER
  valueFrom:
    secretKeyRef:
      name: {{ .existingSecret }}
      key: {{ required "oncall.twilio.phoneNumberKey is required if oncall.twilio.existingSecret is not empty" .phoneNumberKey | quote }}
- name: TWILIO_VERIFY_SERVICE_SID
  valueFrom:
    secretKeyRef:
      name: {{ .existingSecret }}
      key: {{ required "oncall.twilio.verifySidKey is required if oncall.twilio.existingSecret is not empty" .verifySidKey | quote }}
{{- if and .apiKeySidKey .apiKeySecretKey }}
- name: TWILIO_API_KEY_SID
  valueFrom:
    secretKeyRef:
      name: {{ .existingSecret }}
      key: {{ required "oncall.twilio.apiKeySidKey is required if oncall.twilio.existingSecret is not empty" .apiKeySidKey | quote }}
- name: TWILIO_API_KEY_SECRET
  valueFrom:
    secretKeyRef:
      name: {{ .existingSecret }}
      key: {{ required "oncall.twilio.apiKeySecretKey is required if oncall.twilio.existingSecret is not empty" .apiKeySecretKey | quote }}
{{- end }}
{{- else }}
{{- if .accountSid }}
- name: TWILIO_ACCOUNT_SID
  value: {{ .accountSid | quote }}
{{- end }}
{{- if .authToken }}
- name: TWILIO_AUTH_TOKEN
  value: {{ .authToken | quote }}
{{- end }}
{{- if .phoneNumber }}
- name: TWILIO_NUMBER
  value: {{ .phoneNumber | quote }}
{{- end }}
{{- if .verifySid }}
- name: TWILIO_VERIFY_SERVICE_SID
  value: {{ .verifySid | quote }}
{{- end }}
{{- if .apiKeySid }}
- name: TWILIO_API_KEY_SID
  value: {{ .apiKeySid | quote }}
{{- end }}
{{- if .apiKeySecret }}
- name: TWILIO_API_KEY_SECRET
  value: {{ .apiKeySecret | quote }}
{{- end }}
{{- end }}
{{- if .limitPhone }}
- name: PHONE_NOTIFICATIONS_LIMIT
  value: {{ .limitPhone | quote }}
{{- end }}
{{- end }}
{{- end }}

{{- define "snippet.celery.env" }}
{{- if .Values.celery.worker_queue }}
- name: CELERY_WORKER_QUEUE
  value: {{ .Values.celery.worker_queue | quote }}
{{- end }}
{{- if .Values.celery.worker_concurrency }}
- name: CELERY_WORKER_CONCURRENCY
  value: {{ .Values.celery.worker_concurrency | quote }}
{{- end }}
{{- if .Values.celery.worker_max_tasks_per_child }}
- name: CELERY_WORKER_MAX_TASKS_PER_CHILD
  value: {{ .Values.celery.worker_max_tasks_per_child | quote }}
{{- end }}
{{- if .Values.celery.worker_beat_enabled }}
- name: CELERY_WORKER_BEAT_ENABLED
  value: {{ .Values.celery.worker_beat_enabled | quote }}
{{- end }}
{{- if .Values.celery.worker_shutdown_interval }}
- name: CELERY_WORKER_SHUTDOWN_INTERVAL
  value: {{ .Values.celery.worker_shutdown_interval | quote }}
{{- end }}
{{- end }}

{{- define "snippet.grafana.url" -}}
{{ if .Values.grafana.enabled -}}
  http://{{ include "oncall.grafana.fullname" . }}
{{- else -}}
  {{ required "externalGrafana.url is required when not grafana.enabled" .Values.externalGrafana.url }}
{{- end }}
{{- end }}

{{- define "snippet.mysql.env" -}}
- name: MYSQL_HOST
  value: {{ include "snippet.mysql.host" . | quote }}
- name: MYSQL_PORT
  value: {{ include "snippet.mysql.port" . | quote }}
- name: MYSQL_DB_NAME
  value: {{ include "snippet.mysql.db" . | quote }}
- name: MYSQL_USER
{{- if and (not .Values.mariadb.enabled) .Values.externalMysql.existingSecret .Values.externalMysql.usernameKey (not .Values.externalMysql.user) }}
  valueFrom:
    secretKeyRef:
      name: {{ include "snippet.mysql.password.secret.name" . }}
      key: {{ .Values.externalMysql.usernameKey | quote }}
{{- else }}
  value: {{ include "snippet.mysql.user" . | quote }}
{{- end }}
- name: MYSQL_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ include "snippet.mysql.password.secret.name" . }}
      key: {{ include "snippet.mysql.password.secret.key" . | quote }}
{{- end }}

{{- define "snippet.mysql.password.secret.name" -}}
{{ if .Values.mariadb.enabled -}}
  {{ if .Values.mariadb.auth.existingSecret -}}
    {{ .Values.mariadb.auth.existingSecret }}
  {{- else -}}
    {{ include "oncall.mariadb.fullname" . }}
  {{- end }}
{{- else -}}
  {{ if .Values.externalMysql.existingSecret -}}
    {{ .Values.externalMysql.existingSecret }}
  {{- else -}}
    {{ include "oncall.fullname" . }}-mysql-external
  {{- end }}
{{- end }}
{{- end }}

{{- define "snippet.mysql.password.secret.key" -}}
{{ if and (not .Values.mariadb.enabled) .Values.externalMysql.existingSecret .Values.externalMysql.passwordKey -}}
  {{ .Values.externalMysql.passwordKey }}
{{- else -}}
  mariadb-root-password
{{- end }}
{{- end }}

{{- define "snippet.mysql.host" -}}
{{ if and (not .Values.mariadb.enabled) .Values.externalMysql.host -}}
  {{ .Values.externalMysql.host }}
{{- else -}}
  {{ include "oncall.mariadb.fullname" . }}
{{- end }}
{{- end }}

{{- define "snippet.mysql.port" -}}
{{ if and (not .Values.mariadb.enabled) .Values.externalMysql.port -}}
  {{ .Values.externalMysql.port }}
{{- else -}}
  3306
{{- end }}
{{- end }}

{{- define "snippet.mysql.db" -}}
{{ if and (not .Values.mariadb.enabled) .Values.externalMysql.db_name -}}
  {{ .Values.externalMysql.db_name }}
{{- else -}}
  {{ .Values.mariadb.auth.database | default "oncall" }}
{{- end }}
{{- end }}

{{- define "snippet.mysql.user" -}}
{{ if and (not .Values.mariadb.enabled) .Values.externalMysql.user -}}
  {{ .Values.externalMysql.user }}
{{- else -}}
  {{ .Values.mariadb.auth.username | default "root" }}
{{- end }}
{{- end }}

{{- define "snippet.postgresql.env" -}}
- name: DATABASE_TYPE
  value: {{ .Values.database.type | quote }}
- name: DATABASE_HOST
  value: {{ include "snippet.postgresql.host" . | quote }}
- name: DATABASE_PORT
  value: {{ include "snippet.postgresql.port" . | quote }}
- name: DATABASE_NAME
  value: {{ include "snippet.postgresql.db" . | quote }}
- name: DATABASE_USER
  value: {{ include "snippet.postgresql.user" . | quote }}
- name: DATABASE_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ include "snippet.postgresql.password.secret.name" . }}
      key: {{ include "snippet.postgresql.password.secret.key" . | quote }}
{{- end }}

{{- define "snippet.sqlite.env" -}}
- name: DATABASE_TYPE
  value: sqlite3
- name: DATABASE_NAME
  value: /etc/app/oncall.db
{{- end }}

{{- define "snippet.postgresql.password.secret.name" -}}
{{ if .Values.postgresql.enabled -}}
  {{ if .Values.postgresql.auth.existingSecret -}}
    {{ .Values.postgresql.auth.existingSecret }}
  {{- else -}}
    {{ include "oncall.postgresql.fullname" . }}
  {{- end }}
{{- else -}}
  {{ if .Values.externalPostgresql.existingSecret -}}
    {{ .Values.externalPostgresql.existingSecret }}
  {{- else -}}
    {{ include "oncall.fullname" . }}-postgresql-external
  {{- end }}
{{- end }}
{{- end }}

{{- define "snippet.postgresql.password.secret.key" -}}
{{ if .Values.postgresql.enabled -}}
  {{ if .Values.postgresql.auth.existingSecret -}}
    {{ required "postgresql.auth.secretKeys.adminPasswordKey is required if database.type=postgres and postgresql.enabled and postgresql.auth.existingSecret" .Values.postgresql.auth.secretKeys.adminPasswordKey }}
  {{- else -}}
    {{ include "postgresql.userPasswordKey" .Subcharts.postgresql }}
  {{- end }}
{{- else -}}
  {{ if .Values.externalPostgresql.existingSecret -}}
    {{ required "externalPostgresql.passwordKey is required if database.type=postgres and not postgresql.enabled and postgresql.auth.existingSecret" .Values.externalPostgresql.passwordKey }}
  {{- else -}}
    postgres-password
  {{- end }}
{{- end }}
{{- end }}

{{- define "snippet.postgresql.host" -}}
{{ if not .Values.postgresql.enabled -}}
  {{ required "externalPostgresql.host is required if database.type=postgres and not postgresql.enabled" .Values.externalPostgresql.host }}
{{- else -}}
  {{ include "oncall.postgresql.fullname" . }}
{{- end }}
{{- end }}

{{- define "snippet.postgresql.port" -}}
{{ if and (not .Values.postgresql.enabled) .Values.externalPostgresql.port -}}
  {{ .Values.externalPostgresql.port }}
{{- else -}}
  5432
{{- end }}
{{- end }}

{{- define "snippet.postgresql.db" -}}
{{ if not .Values.postgresql.enabled -}}
  {{ .Values.externalPostgresql.db_name | default "oncall" }}
{{- else -}}
  {{ .Values.postgresql.auth.database | default "oncall" }}
{{- end }}
{{- end }}

{{- define "snippet.postgresql.user" -}}
{{ if and (not .Values.postgresql.enabled) -}}
  {{ .Values.externalPostgresql.user | default "postgres" }}
{{- else -}}
  {{ .Values.postgresql.auth.username | default "postgres" }}
{{- end }}
{{- end }}

{{- define "snippet.rabbitmq.env" }}
- name: RABBITMQ_USERNAME
{{- if and (not .Values.rabbitmq.enabled) .Values.externalRabbitmq.existingSecret .Values.externalRabbitmq.usernameKey (not .Values.externalRabbitmq.user) }}
  valueFrom:
    secretKeyRef:
      name: {{ include "snippet.rabbitmq.password.secret.name" . }}
      key: {{ .Values.externalRabbitmq.usernameKey | quote }}
{{- else }}
  value: {{ include "snippet.rabbitmq.user" . | quote }}
{{- end }}
- name: RABBITMQ_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ include "snippet.rabbitmq.password.secret.name" . }}
      key: {{ include "snippet.rabbitmq.password.secret.key" . | quote }}
- name: RABBITMQ_HOST
  value: {{ include "snippet.rabbitmq.host" . | quote }}
- name: RABBITMQ_PORT
  value: {{ include "snippet.rabbitmq.port" . | quote }}
- name: RABBITMQ_PROTOCOL
  value: {{ include "snippet.rabbitmq.protocol" . | quote }}
- name: RABBITMQ_VHOST
  value: {{ include "snippet.rabbitmq.vhost" . | quote }}
{{- end }}

{{- define "snippet.rabbitmq.user" -}}
{{ if not .Values.rabbitmq.enabled -}}
  {{ required "externalRabbitmq.user is required if not rabbitmq.enabled" .Values.externalRabbitmq.user }}
{{- else -}}
  user
{{- end }}
{{- end }}

{{- define "snippet.rabbitmq.host" -}}
{{ if not .Values.rabbitmq.enabled -}}
  {{ required "externalRabbitmq.host is required if not rabbitmq.enabled" .Values.externalRabbitmq.host }}
{{- else -}}
  {{ include "oncall.rabbitmq.fullname" . }}
{{- end }}
{{- end }}

{{- define "snippet.rabbitmq.port" -}}
{{ if and (not .Values.rabbitmq.enabled) .Values.externalRabbitmq.port -}}
  {{ required "externalRabbitmq.port is required if not rabbitmq.enabled" .Values.externalRabbitmq.port }}
{{- else -}}
  5672
{{- end }}
{{- end }}

{{- define "snippet.rabbitmq.protocol" -}}
{{ if and (not .Values.rabbitmq.enabled) .Values.externalRabbitmq.protocol -}}
  {{ .Values.externalRabbitmq.protocol }}
{{- else -}}
  amqp
{{- end }}
{{- end }}

{{- define "snippet.rabbitmq.vhost" -}}
{{ if and (not .Values.rabbitmq.enabled) .Values.externalRabbitmq.vhost -}}
  {{ .Values.externalRabbitmq.vhost }}
{{- end }}
{{- end }}

{{- define "snippet.rabbitmq.password.secret.name" -}}
{{ if .Values.rabbitmq.enabled -}}
  {{ if .Values.rabbitmq.auth.existingPasswordSecret -}}
    {{ .Values.rabbitmq.auth.existingPasswordSecret }}
  {{- else -}}
    {{ include "oncall.rabbitmq.fullname" . }}
  {{- end }}
{{- else -}}
  {{ if .Values.externalRabbitmq.existingSecret -}}
    {{ .Values.externalRabbitmq.existingSecret }}
  {{- else -}}
    {{ include "oncall.fullname" . }}-rabbitmq-external
  {{- end }}
{{- end }}
{{- end }}

{{- define "snippet.rabbitmq.password.secret.key" -}}
{{ if and (not .Values.rabbitmq.enabled) .Values.externalRabbitmq.passwordKey -}}
  {{ .Values.externalRabbitmq.passwordKey }}
{{- else -}}
  rabbitmq-password
{{- end }}
{{- end }}

{{- define "snippet.redis.host" -}}
{{ if not .Values.redis.enabled -}}
  {{ required "externalRedis.host is required if not redis.enabled" .Values.externalRedis.host | quote }}
{{- else -}}
  {{ include "oncall.redis.fullname" . }}-master
{{- end }}
{{- end }}

{{- define "snippet.redis.password.secret.name" -}}
{{ if .Values.redis.enabled -}}
  {{ if .Values.redis.auth.existingSecret -}}
    {{ .Values.redis.auth.existingSecret }}
  {{- else -}}
    {{ include "oncall.redis.fullname" . }}
  {{- end }}
{{- else -}}
  {{ if .Values.externalRedis.existingSecret -}}
    {{ .Values.externalRedis.existingSecret }}
  {{- else -}}
    {{ include "oncall.fullname" . }}-redis-external
  {{- end }}
{{- end }}
{{- end }}

{{- define "snippet.redis.password.secret.key" -}}
{{ if .Values.redis.enabled -}}
  {{ if .Values.redis.auth.existingSecret -}}
    {{ required "redis.auth.existingSecretPasswordKey is required if redis.auth.existingSecret is non-empty" .Values.redis.auth.existingSecretPasswordKey }}
  {{- else -}}
    redis-password
  {{- end }}
{{- else -}}
  {{ if .Values.externalRedis.existingSecret -}}
    {{ required "externalRedis.passwordKey is required if externalRedis.existingSecret is non-empty" .Values.externalRedis.passwordKey }}
  {{- else -}}
    redis-password
  {{- end }}
{{- end }}
{{- end }}

{{- define "snippet.redis.env" -}}
- name: REDIS_HOST
  value: {{ include "snippet.redis.host" . }}
- name: REDIS_PORT
  value: "6379"
- name: REDIS_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ include "snippet.redis.password.secret.name" . }}
      key: {{ include "snippet.redis.password.secret.key" . | quote}}
{{- end }}

{{- define "snippet.broker.env" -}}
{{- if eq .Values.broker.type "redis" }}
{{- include "snippet.redis.env" . }}
{{- else if eq .Values.broker.type "rabbitmq" }}
{{- include "snippet.rabbitmq.env" . }}
{{- else -}}
{{- fail "value for .Values.broker.type must be either 'redis' or 'rabbitmq'" }}
{{- end }}
{{- end }}

{{- define "snippet.db.env" -}}
{{- if eq .Values.database.type "mysql" }}
{{- include "snippet.mysql.env" . }}
{{- else if eq .Values.database.type "postgresql" }}
{{- include "snippet.postgresql.env" . }}
{{- else if eq .Values.database.type "sqlite" -}}
{{- include "snippet.sqlite.env" . }}
{{- else -}}
{{- fail "value for .Values.db.type must be either 'mysql', 'postgresql', or 'sqlite'" }}
{{- end }}
{{- end }}

{{- define "snippet.oncall.smtp.env" -}}
- name: FEATURE_EMAIL_INTEGRATION_ENABLED
  value: {{ .Values.oncall.smtp.enabled | toString | title | quote }}
{{- if .Values.oncall.smtp.enabled }}
- name: EMAIL_HOST
  value: {{ .Values.oncall.smtp.host | quote }}
- name: EMAIL_PORT
  value: {{ .Values.oncall.smtp.port | default "587" | quote }}
- name: EMAIL_HOST_USER
  value: {{ .Values.oncall.smtp.username | quote }}
- name: EMAIL_HOST_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ include "oncall.fullname" . }}-smtp
      key: smtp-password
      optional: true
- name: EMAIL_USE_TLS
  value: {{ .Values.oncall.smtp.tls | default true | toString | title | quote }}
- name: EMAIL_FROM_ADDRESS
  value: {{ .Values.oncall.smtp.fromEmail | quote }}
- name: EMAIL_NOTIFICATIONS_LIMIT
  value: {{ .Values.oncall.smtp.limitEmail | default "200" | quote }}
{{- end }}
{{- end }}

{{- define "snippet.oncall.exporter.env" -}}
{{ if .Values.oncall.exporter.enabled -}}
- name: FEATURE_PROMETHEUS_EXPORTER_ENABLED
  value: {{ .Values.oncall.exporter.enabled | toString | title | quote }}
- name: PROMETHEUS_EXPORTER_SECRET
  valueFrom:
    secretKeyRef:
      name: {{ include "oncall.fullname" . }}-exporter
      key: exporter-secret
      optional: true
{{- else -}}
- name: FEATURE_PROMETHEUS_EXPORTER_ENABLED
  value: {{ .Values.oncall.exporter.enabled | toString | title | quote }}
{{- end }}
{{- end }}
