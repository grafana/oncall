{{- define "snippet.oncall.env" -}}
- name: BASE_URL
  value: https://{{ .Values.base_url }}
- name: SECRET_KEY
  valueFrom:
    secretKeyRef:
      name: {{ template "oncall.fullname" . }}
      key: SECRET_KEY
- name: MIRAGE_SECRET_KEY
  valueFrom:
    secretKeyRef:
      name: {{ template "oncall.fullname" . }}
      key: MIRAGE_SECRET_KEY
- name: MIRAGE_CIPHER_IV
  value: "1234567890abcdef"
- name: DJANGO_SETTINGS_MODULE
  value: "settings.helm"
- name: AMIXR_DJANGO_ADMIN_PATH
  value: "admin"
- name: OSS
  value: "True"
- name: UWSGI_LISTEN
  value: "1024"
{{- end }}

{{- define "snippet.celery.env" -}}
- name: CELERY_WORKER_QUEUE
  value: "default,critical,long,slack,telegram,webhook,celery"
- name: CELERY_WORKER_CONCURRENCY
  value: "1"
- name: CELERY_WORKER_MAX_TASKS_PER_CHILD
  value: "100"
- name: CELERY_WORKER_SHUTDOWN_INTERVAL
  value: "65m"
- name: CELERY_WORKER_BEAT_ENABLED
  value: "True"
{{- end }}

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
{{- if and (not .Values.mariadb.enabled) .Values.externalMysql.db -}}
{{- required "externalMysql.db is required if not mariadb.enabled" .Values.externalMysql.db | quote}}
{{- else -}}
"oncall"
{{- end -}}
{{- end -}}

{{- define "snippet.mysql.user" -}}
{{- if and (not .Values.mariadb.enabled) .Values.externalMysql.user -}}
{{- .Values.externalMysql.user | quote}}
{{- else -}}
"root"
{{- end -}}
{{- end -}}

{{- define "snippet.rabbitmq.env" -}}
- name: RABBITMQ_USERNAME
  value: {{ include "snippet.rabbitmq.user" . }}
- name: RABBITMQ_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ include "snippet.rabbitmq.password.secret.name" . }}
      key: rabbitmq-password
- name: RABBITMQ_HOST
  value: {{ include "snippet.rabbitmq.host" . }}
- name: RABBITMQ_PORT
  value: {{ include "snippet.rabbitmq.port" . }}
- name: RABBITMQ_PROTOCOL
  value: {{ include "snippet.rabbitmq.protocol" . }}
{{- end }}

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

{{- define "snippet.rabbitmq.password.secret.name" -}}
{{- if and (not .Values.rabbitmq.enabled) .Values.externalRabbitmq.password -}}
{{ include "oncall.fullname" . }}-rabbitmq-external
{{- else -}}
{{ include "oncall.rabbitmq.fullname" . }}
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
