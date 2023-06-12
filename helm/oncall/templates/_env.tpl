{{- define "snippet.oncall.env" -}}
- name: BASE_URL
  value: https://{{ .Values.base_url }}
- name: SECRET_KEY
  valueFrom:
    secretKeyRef:
      name: {{ template "snippet.oncall.secret.name" . }}
      key: {{ template "snippet.oncall.secret.secretKey" . }}
- name: MIRAGE_SECRET_KEY
  valueFrom:
    secretKeyRef:
      name: {{ template "snippet.oncall.secret.name" . }}
      key: {{ template "snippet.oncall.secret.mirageSecretKey" . }}
- name: MIRAGE_CIPHER_IV
  value: "{{ .Values.oncall.mirageCipherIV | default "1234567890abcdef" }}"
- name: DJANGO_SETTINGS_MODULE
  value: "settings.helm"
- name: AMIXR_DJANGO_ADMIN_PATH
  value: "admin"
- name: OSS
  value: "True"
{{- template "snippet.oncall.uwsgi" . }}
- name: BROKER_TYPE
  value: {{ .Values.broker.type | default "rabbitmq" }}
- name: GRAFANA_API_URL
  value: {{ include "snippet.grafana.url" . }}
{{- end -}}

{{- define "snippet.oncall.secret.name" -}}
{{- if .Values.oncall.secrets.existingSecret -}}
{{ .Values.oncall.secrets.existingSecret }}
{{- else -}}
{{ template "oncall.fullname" . }}
{{- end -}}
{{- end -}}

{{- define "snippet.oncall.secret.secretKey" -}}
{{- if .Values.oncall.secrets.existingSecret -}}
{{ required "oncall.secrets.secretKey is required if oncall.secret.existingSecret is not empty" .Values.oncall.secrets.secretKey }}
{{- else -}}
SECRET_KEY
{{- end -}}
{{- end -}}

{{- define "snippet.oncall.secret.mirageSecretKey" -}}
{{- if .Values.oncall.secrets.existingSecret -}}
{{ required "oncall.secrets.mirageSecretKey is required if oncall.secret.existingSecret is not empty" .Values.oncall.secrets.mirageSecretKey }}
{{- else -}}
MIRAGE_SECRET_KEY
{{- end -}}
{{- end -}}

{{- define "snippet.oncall.uwsgi" -}}
{{- if .Values.uwsgi -}}
  {{- range $key, $value := .Values.uwsgi }}
- name: UWSGI_{{ $key | upper | replace "-" "_" }}
  value: {{ $value | quote }}
  {{- end -}}
{{- end -}}
{{- end -}}

{{- define "snippet.oncall.slack.env" -}}
{{- if .Values.oncall.slack.enabled -}}
- name: FEATURE_SLACK_INTEGRATION_ENABLED
  value: {{ .Values.oncall.slack.enabled | toString | title | quote }}
- name: SLACK_SLASH_COMMAND_NAME
  value: "/{{ .Values.oncall.slack.commandName | default "oncall" }}"
{{- if .Values.oncall.slack.existingSecret }}
- name: SLACK_CLIENT_OAUTH_ID
  valueFrom:
    secretKeyRef:
      name: {{ .Values.oncall.slack.existingSecret }}
      key: {{ required "oncall.slack.clientIdKey is required if oncall.slack.existingSecret is not empty" .Values.oncall.slack.clientIdKey }}
- name: SLACK_CLIENT_OAUTH_SECRET
  valueFrom:
    secretKeyRef:
      name: {{ .Values.oncall.slack.existingSecret }}
      key: {{ required "oncall.slack.clientSecretKey is required if oncall.slack.existingSecret is not empty" .Values.oncall.slack.clientSecretKey }}
- name: SLACK_SIGNING_SECRET
  valueFrom:
    secretKeyRef:
      name: {{ .Values.oncall.slack.existingSecret }}
      key: {{ required "oncall.slack.signingSecretKey is required if oncall.slack.existingSecret is not empty" .Values.oncall.slack.signingSecretKey }}
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
{{- else -}}
- name: FEATURE_SLACK_INTEGRATION_ENABLED
  value: {{ .Values.oncall.slack.enabled | toString | title | quote }}
{{- end -}}
{{- end -}}

{{- define "snippet.oncall.telegram.env" -}}
{{- if .Values.oncall.telegram.enabled -}}
- name: FEATURE_TELEGRAM_INTEGRATION_ENABLED
  value: {{ .Values.oncall.telegram.enabled | toString | title | quote }}
- name: TELEGRAM_WEBHOOK_HOST
  value: {{ .Values.oncall.telegram.webhookUrl | default "" | quote }}
{{- if .Values.oncall.telegram.existingSecret }}
- name: TELEGRAM_TOKEN
  valueFrom:
    secretKeyRef:
      name: {{ .Values.oncall.telegram.existingSecret }}
      key: {{ required "oncall.telegram.tokenKey is required if oncall.telegram.existingSecret is not empty" .Values.oncall.telegram.tokenKey }}
{{- else }}
- name: TELEGRAM_TOKEN
  value: {{ .Values.oncall.telegram.token | default "" | quote }}
{{- end }}
{{- else -}}
- name: FEATURE_TELEGRAM_INTEGRATION_ENABLED
  value: {{ .Values.oncall.telegram.enabled | toString | title | quote }}
{{- end -}}
{{- end -}}

{{- define "snippet.oncall.twilio.env" -}}
{{- with .Values.oncall.twilio -}}
{{- if .accountSid }}
- name: TWILIO_ACCOUNT_SID
  value: {{ .accountSid | quote }}
{{- end -}}
{{- if .existingSecret }}
- name: TWILIO_AUTH_TOKEN
  valueFrom:
    secretKeyRef:
      name: {{ .existingSecret }}
      key: {{ required ".authTokenKey is required if .existingSecret is not empty" .authTokenKey }}
- name: TWILIO_NUMBER
  valueFrom:
    secretKeyRef:
      name: {{ .existingSecret }}
      key: {{ required ".phoneNumberKey is required if .existingSecret is not empty" .phoneNumberKey }}
- name: TWILIO_VERIFY_SERVICE_SID
  valueFrom:
    secretKeyRef:
      name: {{ .existingSecret }}
      key: {{ required ".verifySidKey is required if .existingSecret is not empty" .verifySidKey }}
- name: TWILIO_API_KEY_SID
  valueFrom:
    secretKeyRef:
      name: {{ .existingSecret }}
      key: {{ required ".apiKeySidKey is required if .existingSecret is not empty" .apiKeySidKey }}
- name: TWILIO_API_KEY_SECRET
  valueFrom:
    secretKeyRef:
      name: {{ .existingSecret }}
      key: {{ required ".apiKeySecretKey is required if .existingSecret is not empty" .apiKeySecretKey }}
{{- else }}
{{- if .authToken }}
- name: TWILIO_AUTH_TOKEN
  value: {{ .authToken | quote }}
{{- end -}}
{{- if .phoneNumber }}
- name: TWILIO_NUMBER
  value: {{ .phoneNumber | quote }}
{{- end -}}
{{- if .verifySid }}
- name: TWILIO_VERIFY_SERVICE_SID
  value: {{ .verifySid | quote }}
{{- end -}}
{{- if .apiKeySid }}
- name: TWILIO_API_KEY_SID
  value: {{ .apiKeySid | quote }}
{{- end -}}
{{- if .apiKeySecret }}
- name: TWILIO_API_KEY_SECRET
  value: {{ .apiKeySecret | quote }}
{{- end -}}
{{- if .limitPhone }}
- name: PHONE_NOTIFICATIONS_LIMIT
  value: {{ .limitPhone | quote }}
{{- end -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{- define "snippet.celery.env" -}}
{{- if .Values.celery.worker_queue }}
- name: CELERY_WORKER_QUEUE
  value: {{ .Values.celery.worker_queue }}
{{- end -}}
{{- if .Values.celery.worker_concurrency }}
- name: CELERY_WORKER_CONCURRENCY
  value: {{ .Values.celery.worker_concurrency | quote }}
{{- end -}}
{{- if .Values.celery.worker_max_tasks_per_child }}
- name: CELERY_WORKER_MAX_TASKS_PER_CHILD
  value: {{ .Values.celery.worker_max_tasks_per_child | quote }}
{{- end -}}
{{- if .Values.celery.worker_beat_enabled }}
- name: CELERY_WORKER_BEAT_ENABLED
  value: {{ .Values.celery.worker_beat_enabled | quote }}
{{- end -}}
{{- if .Values.celery.worker_shutdown_interval }}
- name: CELERY_WORKER_SHUTDOWN_INTERVAL
  value: {{ .Values.celery.worker_shutdown_interval }}
{{- end -}}
{{- end -}}

{{- define "snippet.grafana.url" -}}
{{- if .Values.externalGrafana.url -}}
{{- .Values.externalGrafana.url | quote }}
{{- else if .Values.grafana.enabled -}}
http://{{ include "oncall.grafana.fullname" . }}
{{- else -}}
{{- required "externalGrafana.url is required when not grafana.enabled" .Values.externalGrafana.url | quote }}
{{- end -}}
{{- end -}}

{{- define "snippet.mysql.env" -}}
- name: MYSQL_HOST
  value: {{ include "snippet.mysql.host" . }}
- name: MYSQL_PORT
  value: {{ include "snippet.mysql.port" . }}
- name: MYSQL_DB_NAME
  value: {{ include "snippet.mysql.db" . }}
- name: MYSQL_USER
  value: {{ include "snippet.mysql.user" . }}
- name: MYSQL_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ include "snippet.mysql.password.secret.name" . }}
      key: mariadb-root-password
{{- end }}

{{- define "snippet.mysql.password.secret.name" -}}
{{- if and (not .Values.mariadb.enabled) .Values.externalMysql.password -}}
{{ include "oncall.fullname" . }}-mysql-external
{{- else -}}
{{ include "oncall.mariadb.fullname" . }}
{{- end -}}
{{- end -}}

{{- define "snippet.mysql.host" -}}
{{- if and (not .Values.mariadb.enabled) .Values.externalMysql.host -}}
{{- required "externalMysql.host is required if not mariadb.enabled" .Values.externalMysql.host | quote }}
{{- else -}}
{{ include "oncall.mariadb.fullname" . }}
{{- end -}}
{{- end -}}

{{- define "snippet.mysql.port" -}}
{{- if and (not .Values.mariadb.enabled) .Values.externalMysql.port -}}
{{- required "externalMysql.port is required if not mariadb.enabled"  .Values.externalMysql.port | quote }}
{{- else -}}
"3306"
{{- end -}}
{{- end -}}

{{- define "snippet.mysql.db" -}}
{{- if and (not .Values.mariadb.enabled) .Values.externalMysql.db_name -}}
{{- required "externalMysql.db_name is required if not mariadb.enabled" .Values.externalMysql.db_name | quote}}
{{- else -}}
{{- .Values.mariadb.auth.database | default "oncall" | quote -}}
{{- end -}}
{{- end -}}

{{- define "snippet.mysql.user" -}}
{{- if and (not .Values.mariadb.enabled) .Values.externalMysql.user -}}
{{- .Values.externalMysql.user | quote }}
{{- else -}}
{{- .Values.mariadb.auth.username | default "root" | quote -}}
{{- end -}}
{{- end -}}

{{- define "snippet.postgresql.env" -}}
- name: DATABASE_TYPE
  value: {{ .Values.database.type }}
- name: DATABASE_HOST
  value: {{ include "snippet.postgresql.host" . }}
- name: DATABASE_PORT
  value: {{ include "snippet.postgresql.port" . }}
- name: DATABASE_NAME
  value: {{ include "snippet.postgresql.db" . }}
- name: DATABASE_USER
  value: {{ include "snippet.postgresql.user" . }}
- name: DATABASE_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ include "snippet.postgresql.password.secret.name" . }}
      key: {{ include "snippet.postgresql.password.secret.key" . }}
{{- end }}

{{- define "snippet.postgresql.password.secret.name" -}}
{{- if and (not .Values.postgresql.enabled) .Values.externalPostgresql.password -}}
{{ include "oncall.fullname" . }}-postgresql-external
{{- else if and (not .Values.postgresql.enabled) .Values.externalPostgresql.existingSecret -}}
{{ .Values.externalPostgresql.existingSecret }}
{{- else -}}
{{ include "oncall.postgresql.fullname" . }}
{{- end -}}
{{- end -}}

{{- define "snippet.postgresql.password.secret.key" -}}
{{- if and (not .Values.postgresql.enabled) .Values.externalPostgresql.passwordKey -}}
{{ .Values.externalPostgresql.passwordKey }}
{{- else if .Values.postgresql.enabled -}}
{{ include "postgresql.userPasswordKey" .Subcharts.postgresql }}
{{- else -}}
"postgres-password"
{{- end -}}
{{- end -}}

{{- define "snippet.postgresql.host" -}}
{{- if and (not .Values.postgresql.enabled) .Values.externalPostgresql.host -}}
{{- required "externalPostgresql.host is required if not postgresql.enabled" .Values.externalPostgresql.host | quote }}
{{- else -}}
{{ include "oncall.postgresql.fullname" . }}
{{- end -}}
{{- end -}}

{{- define "snippet.postgresql.port" -}}
{{- if and (not .Values.postgresql.enabled) .Values.externalPostgresql.port -}}
{{- required "externalPostgresql.port is required if not postgresql.enabled"  .Values.externalPostgresql.port | quote }}
{{- else -}}
"5432"
{{- end -}}
{{- end -}}

{{- define "snippet.postgresql.db" -}}
{{- if and (not .Values.postgresql.enabled) .Values.externalPostgresql.db_name -}}
{{- required "externalPostgresql.db_name is required if not postgresql.enabled" .Values.externalPostgresql.db_name | quote}}
{{- else -}}
{{- .Values.postgresql.auth.database | default "oncall" | quote -}}
{{- end -}}
{{- end -}}

{{- define "snippet.postgresql.user" -}}
{{- if and (not .Values.postgresql.enabled) .Values.externalPostgresql.user -}}
{{- .Values.externalPostgresql.user | quote}}
{{- else -}}
{{- .Values.postgresql.auth.username | default "postgres" | quote -}}
{{- end -}}
{{- end -}}

{{- define "snippet.rabbitmq.env" -}}
{{- if eq .Values.broker.type "rabbitmq" -}}
{{- if and (not .Values.rabbitmq.enabled) .Values.externalRabbitmq.existingSecret .Values.externalRabbitmq.usernameKey (not .Values.externalRabbitmq.user) }}
- name: RABBITMQ_USERNAME
  valueFrom:
    secretKeyRef:
      name: {{ include "snippet.rabbitmq.password.secret.name" . }}
      key: {{ .Values.externalRabbitmq.usernameKey }}
{{- else }}
- name: RABBITMQ_USERNAME
  value: {{ include "snippet.rabbitmq.user" . }}
{{- end }}
- name: RABBITMQ_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ include "snippet.rabbitmq.password.secret.name" . }}
      key: {{ include "snippet.rabbitmq.password.secret.key" . }}
- name: RABBITMQ_HOST
  value: {{ include "snippet.rabbitmq.host" . }}
- name: RABBITMQ_PORT
  value: {{ include "snippet.rabbitmq.port" . }}
- name: RABBITMQ_PROTOCOL
  value: {{ include "snippet.rabbitmq.protocol" . }}
- name: RABBITMQ_VHOST
  value: {{ include "snippet.rabbitmq.vhost" . }}
{{- end }}
{{- end -}}

{{- define "snippet.rabbitmq.user" -}}
{{- if and (not .Values.rabbitmq.enabled) .Values.externalRabbitmq.user -}}
{{- required "externalRabbitmq.user is required if not rabbitmq.enabled" .Values.externalRabbitmq.user | quote }}
{{- else -}}
"user"
{{- end -}}
{{- end -}}

{{- define "snippet.rabbitmq.host" -}}
{{- if and (not .Values.rabbitmq.enabled) .Values.externalRabbitmq.host -}}
{{- required "externalRabbitmq.host is required if not rabbitmq.enabled" .Values.externalRabbitmq.host | quote }}
{{- else -}}
{{ include "oncall.rabbitmq.fullname" . }}
{{- end -}}
{{- end -}}

{{- define "snippet.rabbitmq.port" -}}
{{- if and (not .Values.rabbitmq.enabled) .Values.externalRabbitmq.port -}}
{{- required "externalRabbitmq.port is required if not rabbitmq.enabled" .Values.externalRabbitmq.port | quote }}
{{- else -}}
"5672"
{{- end -}}
{{- end -}}

{{- define "snippet.rabbitmq.protocol" -}}
{{- if and (not .Values.rabbitmq.enabled) .Values.externalRabbitmq.protocol -}}
{{ .Values.externalRabbitmq.protocol | quote }}
{{- else -}}
"amqp"
{{- end -}}
{{- end -}}

{{- define "snippet.rabbitmq.vhost" -}}
{{- if and (not .Values.rabbitmq.enabled) .Values.externalRabbitmq.vhost -}}
{{ .Values.externalRabbitmq.vhost | quote }}
{{- else -}}
""
{{- end -}}
{{- end -}}

{{- define "snippet.rabbitmq.password.secret.name" -}}
{{- if and (not .Values.rabbitmq.enabled) .Values.externalRabbitmq.password -}}
{{ include "oncall.fullname" . }}-rabbitmq-external
{{- else if and (not .Values.rabbitmq.enabled) .Values.externalRabbitmq.existingSecret -}}
{{ .Values.externalRabbitmq.existingSecret }}
{{- else -}}
{{ include "oncall.rabbitmq.fullname" . }}
{{- end -}}
{{- end -}}

{{- define "snippet.rabbitmq.password.secret.key" -}}
{{- if and (not .Values.rabbitmq.enabled) .Values.externalRabbitmq.passwordKey -}}
{{ .Values.externalRabbitmq.passwordKey }}
{{- else -}}
rabbitmq-password
{{- end -}}
{{- end -}}

{{- define "snippet.redis.host" -}}
{{- if and (not .Values.redis.enabled) .Values.externalRedis.host -}}
{{- required "externalRedis.host is required if not redis.enabled" .Values.externalRedis.host | quote }}
{{- else -}}
{{ include "oncall.redis.fullname" . }}-master
{{- end -}}
{{- end -}}

{{- define "snippet.redis.password.secret.name" -}}
{{- if and (not .Values.redis.enabled) .Values.externalRedis.password -}}
{{ include "oncall.fullname" . }}-redis-external
{{- else -}}
{{ include "oncall.redis.fullname" . }}
{{- end -}}
{{- end -}}

{{- define "snippet.redis.env" -}}
- name: REDIS_HOST
  value: {{ include "snippet.redis.host" . }}
- name: REDIS_PORT
  value: "6379"
- name: REDIS_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ template "snippet.redis.password.secret.name" . }}
      key: redis-password
{{- end }}

{{- define "snippet.oncall.smtp.env" -}}
{{- if .Values.oncall.smtp.enabled -}}
- name: FEATURE_EMAIL_INTEGRATION_ENABLED
  value: {{ .Values.oncall.smtp.enabled | toString | title | quote }}
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
{{- else -}}
- name: FEATURE_EMAIL_INTEGRATION_ENABLED
  value: {{ .Values.oncall.smtp.enabled | toString | title | quote }}
{{- end -}}
{{- end }}

{{- define "snippet.oncall.exporter.env" -}}
{{- if .Values.oncall.exporter.enabled -}}
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
{{- end -}}
{{- end }}
