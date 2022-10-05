{{- define "template.oncall.celery.deployment" -}}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "oncall.celery.fullname" . }}
  labels:
    {{- include "oncall.celery.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.celery.replicaCount }}
  selector:
    matchLabels:
      {{- include "oncall.celery.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      {{- with .Values.podAnnotations }}
      annotations:
        random-annotation: {{ randAlphaNum 10 | lower }}
        {{- toYaml . | nindent 8 }}
      {{- end }}
      labels:
        {{- include "oncall.celery.selectorLabels" . | nindent 8 }}
    spec:
      {{- with .Values.imagePullSecrets }}
      imagePullSecrets:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      serviceAccountName: {{ include "oncall.serviceAccountName" . }}
      securityContext:
        {{- toYaml .Values.podSecurityContext | nindent 8 }}
      initContainers:
      {{- include "oncall.mariadb.wait-for-db" . | indent 8 }}
      containers:
        - name: {{ .Chart.Name }}
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
          command: ["./celery_with_exporter.sh"]
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          env:
            {{- include "snippet.celery.env" . | nindent 12 }}
            {{- include "snippet.oncall.env" . | nindent 12 }}
            {{- include "snippet.oncall.slack.env" . | nindent 12 }}
            {{- include "snippet.oncall.telegram.env" . | nindent 12 }}
            {{- include "snippet.mysql.env" . | nindent 12 }}
            {{- include "snippet.rabbitmq.env" . | nindent 12 }}
            {{- include "snippet.redis.env" . | nindent 12 }}
            {{- if .Values.env }}
              {{- toYaml .Values.env | nindent 12 }}
            {{- end }}
          {{- if .Values.celery.livenessProbe.enabled }}
          livenessProbe:
            exec:
              command: [
                "bash",
                "-c",
                "celery -A engine inspect ping -d celery@$HOSTNAME"
              ]
            initialDelaySeconds: {{ .Values.celery.livenessProbe.initialDelaySeconds }}
            periodSeconds: {{ .Values.celery.livenessProbe.periodSeconds }}
            timeoutSeconds: {{ .Values.celery.livenessProbe.timeoutSeconds }}
          {{- end }}
          resources:
            {{- toYaml .Values.celery.resources | nindent 12 }}
{{- end}}