load('ext://uibutton', 'cmd_button', 'location', 'text_input', 'bool_input')
running_under_parent_tiltfile = os.getenv("TILT_PARENT", "false") == "true"
# The user/pass that you will login to Grafana with
grafana_admin_user_pass = os.getenv("GRAFANA_ADMIN_USER_PASS", "oncall")
grafana_image_tag = os.getenv("GRAFANA_IMAGE_TAG", "latest")
e2e_tests_cmd=os.getenv("E2E_TESTS_CMD", "cd grafana-plugin && yarn test:e2e")
twilio_values=[
    "oncall.twilio.accountSid=" + os.getenv("TWILIO_ACCOUNT_SID", ""),
    "oncall.twilio.authToken=" + os.getenv("TWILIO_AUTH_TOKEN", ""),
    "oncall.twilio.phoneNumber=" + os.getenv("TWILIO_PHONE_NUMBER", ""),
    "oncall.twilio.verifySid=" + os.getenv("TWILIO_VERIFY_SID", ""),
]
is_ci=config.tilt_subcommand == "ci"
# HELM_PREFIX must be "oncall-dev" as it is hardcoded in dev/helm-local.yml
HELM_PREFIX = "oncall-dev"
# Use docker registery generated by ctlptl (dev/kind-config.yaml)
DOCKER_REGISTRY = "localhost:63628/"

if not running_under_parent_tiltfile:
    # Load the custom Grafana extensions
    v1alpha1.extension_repo(
        name="grafana-tilt-extensions",
        ref="v1.2.0",
        url="https://github.com/grafana/tilt-extensions",
    )
v1alpha1.extension(
    name="grafana", repo_name="grafana-tilt-extensions", repo_path="grafana"
)

load("ext://grafana", "grafana")
load("ext://configmap", "configmap_create")
load("ext://docker_build_sub", "docker_build_sub")

# Tell ops-devenv/Tiltifle where our plugin.json file lives
plugin_file = os.path.abspath("grafana-plugin/src/plugin.json")


def plugin_json():
    return plugin_file


allow_k8s_contexts(["kind-kind"])

# Build the image including frontend folder for pytest
docker_build_sub(
    "localhost:63628/oncall/engine:dev",
    context="./engine",
    cache_from=["grafana/oncall:latest", "grafana/oncall:dev"],
    ignore=["./test-results/", "./grafana-plugin/dist/", "./grafana-plugin/e2e-tests/"],
    child_context=".",
    target="dev",
    extra_cmds=["ADD ./grafana-plugin/src/plugin.json /etc/grafana-plugin/src/plugin.json"],
    live_update=[
        sync("./engine/", "/etc/app"),
        run(
            "cd /etc/app && pip install pip-tools && pip-sync",
            trigger="./engine/requirements.txt",
        ),
    ],
)

# Build the plugin in the background
local_resource(
    "build-ui",
    labels=["OnCallUI"],
    serve_cmd="cd grafana-plugin && yarn watch",
    allow_parallel=True,
)

local_resource(
    "e2e-tests",
    labels=["E2eTests"],
    cmd=e2e_tests_cmd,
    trigger_mode=TRIGGER_MODE_MANUAL,
    auto_init=is_ci,
    resource_deps=["build-ui", "grafana", "grafana-oncall-app-provisioning-configmap", "engine", "celery"]
)

cmd_button(
    name="E2E Tests - headless run",
    # TODO: revert
    argv=["sh", "-c", "yarn --cwd ./grafana-plugin test:e2e-expensive $STOP_ON_FIRST_FAILURE $TESTS_FILTER"],
    text="Restart headless run",
    resource="e2e-tests",
    icon_name="replay",
    inputs=[
        text_input("BROWSERS", "Browsers (e.g. \"chromium,firefox,webkit\")", "chromium", "chromium,firefox,webkit"),
        text_input("TESTS_FILTER", "Test filter (e.g. \"timezones.test quality.test\")", "", "Test file names to run"), 
        bool_input("STOP_ON_FIRST_FAILURE", "Stop on first failure", True, "-x", ""),
    ]
)

cmd_button(
    name="E2E Tests - open watch mode",
    # TODO: revert
    argv=["sh", "-c", "yarn --cwd grafana-plugin test:e2e-expensive:watch"],
    text="Open watch mode",
    resource="e2e-tests",
    icon_name="visibility",
)

cmd_button(
    name="E2E Tests - show report",
    argv=["sh", "-c", "yarn --cwd grafana-plugin playwright show-report"],
    text="Show last HTML report",
    resource="e2e-tests",
    icon_name="assignment",
)

cmd_button(
    name="E2E Tests - stop current run",
    argv=["sh", "-c", "kill -9 $(pgrep -f test:e2e)"],
    text="Stop",
    resource="e2e-tests",
    icon_name="dangerous",
)

yaml = helm("helm/oncall", name=HELM_PREFIX, values=["./dev/helm-local.yml", "./dev/helm-local.dev.yml"], set=twilio_values)

k8s_yaml(yaml)

# Generate and load the grafana deploy yaml
configmap_create(
    "grafana-oncall-app-provisioning",
    namespace="default",
    from_file="dev/grafana/provisioning/plugins/grafana-oncall-app-provisioning.yaml",
)

k8s_resource(
    objects=["grafana-oncall-app-provisioning:configmap"],
    new_name="grafana-oncall-app-provisioning-configmap",
    resource_deps=["build-ui", "engine"],
    labels=["Grafana"],
)

# Use separate grafana helm chart
if not running_under_parent_tiltfile:
    grafana(
        grafana_version=grafana_image_tag,
        context="grafana-plugin",
        plugin_files=["grafana-plugin/src/plugin.json"],
        namespace="default",
        deps=["grafana-oncall-app-provisioning-configmap", "build-ui", "engine"],
        extra_env={
            "GF_SECURITY_ADMIN_PASSWORD": "oncall",
            "GF_SECURITY_ADMIN_USER": "oncall",
            "GF_AUTH_ANONYMOUS_ENABLED": "false",
        },
    )

k8s_resource(
    workload="celery",
    resource_deps=["mariadb", "redis-master"],
    labels=["OnCallBackend"],
)
k8s_resource(
    workload="engine",
    port_forwards=8080,
    resource_deps=["mariadb", "redis-master"],
    labels=["OnCallBackend"],
)
k8s_resource(workload="redis-master", labels=["OnCallDeps"])
k8s_resource(
    workload="mariadb",
    port_forwards='3307:3306', # <host_port>:<container_port>
    labels=["OnCallDeps"],
)


# name all tilt resources after the k8s object namespace + name
def resource_name(id):
    return id.name.replace(HELM_PREFIX + "-", "")

workload_to_resource_function(resource_name)
