
# Build dependancies for OnCall
local_resource('yarn-install', 'yarn install')
local_resource("Build Oncall Frontend", 
        cmd='yarn build:dev',
        # serve_cmd='yarn dev',
        deps = ["grafana-plugin/src"],
        dir='grafana-plugin',
        resource_deps=['yarn-install'])

docker_build("oncall/engine:latest", "./engine", target = 'dev')

def extra_helm_values():
  extra_values = []
  if os.getenv('START_GRAFANA', 'true') == 'false':
    extra_values.append(['grafana.enabled=false',
                         'externalGrafana.url=http://grafana:3000'])
  else:
    extra_values.append('global.postgresql.auth.postgresPassword=postgres')

  return extra_values

yaml = helm(
  'helm/oncall',
  # The release name, equivalent to helm --name
  name='helm-testing',
  set=extra_helm_values(),
  # The values file to substitute into the chart.
  values=['./helm/simple.yml',
          './helm/values-arm64.yml',
          './helm/values-local-image.yml',
          './helm/values-grafana-anonymous.yml'])
k8s_yaml(yaml)

k8s_resource(workload='helm-testing-grafana', port_forwards=3000)
