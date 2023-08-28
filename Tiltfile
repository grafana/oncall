# HELM_PREFIX must be "oncall-dev" as it is hardcoded in dev/helm-local.yml
HELM_PREFIX="oncall-dev"
# Use docker registery generated by ctlptl (dev/kind-config.yaml)
DOCKER_REGISTRY="localhost:63628/"

# Load the custom Grafana extensions
v1alpha1.extension_repo(name='grafana-tilt-extensions', url='https://github.com/grafana/tilt-extensions')
v1alpha1.extension(name='grafana', repo_name='grafana-tilt-extensions', repo_path='grafana')
load('ext://grafana', 'grafana')
load('ext://configmap', 'configmap_create')

# Tell ops-devenv/Tiltifle where our plugin.json file lives
plugin_file = os.path.abspath('grafana-plugin/src/plugin.json')
def plugin_json():
    return plugin_file

allow_k8s_contexts(["kind-kind"])

docker_build(
     		 "localhost:63628/oncall/engine:dev", 
     		 "./engine", 
     		 target = 'prod',
		     live_update=[
			 	sync('./engine/', '/etc/app'),
				run('cd /etc/app && pip install -r requirements.txt',
					trigger='./engine/requirements.txt'),
				run('OnCall backend is updated')
			 ]
)

# Build the plugin in the background
# docker_compose('grafana-plugin/docker-compose-dev.yaml')
local_resource('build-ui',
				labels=['OnCallUI'],
				cmd='cd grafana-plugin && yarn install && yarn build:dev',
				serve_cmd='cd grafana-plugin && ONCALL_API_URL=http://oncall-dev-engine:8080 yarn watch',
				allow_parallel=True)

yaml = helm(
  'helm/oncall',
  name=HELM_PREFIX,
  values=['./dev/helm-local.yml'])

k8s_yaml(yaml)

# Generate and load the grafana deploy yaml
configmap_create('grafana-oncall-app-provisioning',
				  namespace='default',
				  from_file='dev/grafana/provisioning/plugins/grafana-oncall-app-provisioning.yaml')

k8s_resource(objects=['grafana-oncall-app-provisioning:configmap'],
    		new_name='grafana-oncall-app-provisioning-configmap',
			labels=['Grafana'])

# Use separate grafana helm chart
if os.getenv('START_GRAFANA', 'true') != 'false':
	grafana(context='grafana-plugin',
			plugin_files = ['grafana-plugin/src/plugin.json'],
			namespace='default',
			deps = ['grafana-oncall-app-provisioning-configmap', 'build-ui'],
			extra_env={
				'GF_SECURITY_ADMIN_PASSWORD': 'oncall',
				'GF_SECURITY_ADMIN_USER': 'oncall',
                'GF_AUTH_ANONYMOUS_ENABLED': 'false',
		    },
			)

k8s_resource(workload='celery', resource_deps=['mariadb', 'redis-master'], labels=['OnCallBackend'])
k8s_resource(workload='engine', port_forwards=8080, resource_deps=['mariadb', 'redis-master'], labels=['OnCallBackend'])
k8s_resource(workload='redis-master', labels=['OnCallDeps'])
k8s_resource(workload='mariadb', labels=['OnCallDeps'])

# name all tilt resources after the k8s object namespace + name
def resource_name(id):
  return id.name.replace(HELM_PREFIX + '-', '')

workload_to_resource_function(resource_name)
