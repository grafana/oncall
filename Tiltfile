HELM_PREFIX='helm-testing'

# Build dependancies for OnCall
local_resource('yarn-install', 'yarn install', labels=['OnCallDeps'])
local_resource("build-oncall-frontend", 
        cmd='yarn build:dev',
        # serve_cmd='yarn dev',
        deps = ["grafana-plugin/src"],
        dir='grafana-plugin',
        resource_deps=['yarn-install'],
        labels=['OnCallDeps'])

docker_build("oncall/engine:latest", "./engine", 
              target = 'dev', 
              entrypoint = 'uwsgi --disable-logging --py-autoreload 3 --ini uwsgi.ini')

def extra_helm_values():
  extra_values = ['externalGrafana.url=http://grafana:3000']
  if os.getenv('START_GRAFANA', 'true') == 'false':
    extra_values.append('grafana.enabled=false')
  else:
    extra_values.append('global.postgresql.auth.postgresPassword=postgres')

  return extra_values

yaml = helm(
  'helm/oncall',
  # The release name, equivalent to helm --name
  name=HELM_PREFIX,
  set=extra_helm_values(),
  # The values file to substitute into the chart.
  values=['./helm/simple.yml',
          './helm/values-arm64.yml',
          './helm/values-local-image.yml',
          './helm/values-grafana-anonymous.yml'])
k8s_yaml(yaml)

k8s_resource(workload='grafana', port_forwards=3000, resource_deps=['oncall-engine'], labels=['Grafana'])
k8s_resource(workload='oncall-celery', resource_deps=['postgresql', 'rabbitmq', 'redis-master', 'redis-replicas'], labels=['OnCallBackend'])
k8s_resource(workload='oncall-engine', resource_deps=['postgresql', 'rabbitmq', 'redis-master', 'redis-replicas'], labels=['OnCallBackend'])
k8s_resource(workload='redis-master', labels=['OnCallDeps'])
k8s_resource(workload='postgresql', labels=['OnCallDeps'])
k8s_resource(workload='redis-replicas', labels=['OnCallDeps'])
k8s_resource(workload='rabbitmq', labels=['OnCallDeps'])

# k8s_resource(workload='', labels=['OnCall'])

# k8s_resource(workload='', labels=['OnCall'])
# k8s_resource(workload='', labels=['OnCall'])
# k8s_resource(workload='', labels=['OnCall'])

# name all tilt resources after the k8s object namespace + name
def resource_name(id):
  return id.name.replace(HELM_PREFIX + '-', '')

workload_to_resource_function(resource_name)