#!/usr/bin/env bash
# This script provisions plugin settings. If the plugin config changes
# this will need to be updated

BASE_URL="http://oncall:oncall@localhost:3000"
ENGINE_URL="http://localhost:8080"

# https://stackoverflow.com/questions/51974418/wait-until-a-condition-is-met-in-bash-script
function wait_for() {
    timeout=$1
    shift 1
    until [ $timeout -le 0 ] || ("$@" &> /dev/null); do
        echo -n '.'
        sleep 3
        timeout=$(( timeout - 1 ))
    done
    if [ $timeout -le 0 ]; then
        return 1
    fi
}

function is_grafana_up() {
    curl $BASE_URL/api/auth/keys
    return $?
}

echo -n 'Creating and setting api keys. Waiting for grafana to start...'
wait_for 100 is_grafana_up

SERVICE_ACCOUNT_ID=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "{\"name\":\"sa-autogen-OnCall\", \"role\": \"Admin\"}" \
        ${BASE_URL}/api/serviceaccounts \
        | jq -r ".id")

API_KEY=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "{\"name\":\"oncall\"}" \
        ${BASE_URL}/api/serviceaccounts/${SERVICE_ACCOUNT_ID}/tokens \
        | jq -r ".key")

echo $API_KEY >| .last-api-key

ONCALL_TOKEN=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -H "X-Instance-Context: { \"grafana_token\": \"${API_KEY}\" }" \
        ${ENGINE_URL}/api/internal/v1/plugin/self-hosted/install \
        | jq -r ".onCallToken")

# Get existing plugin settings to merge with our new settings
curl -s -X GET \
	-H "Accept: application/json" \
  ${BASE_URL}/api/plugins/grafana-oncall-app/settings | jq -r "{ jsonData }" >| .settings

# Merge json
jq -s --arg APIKEY ${API_KEY} --arg ONCALLTOKEN ${ONCALL_TOKEN} \
	'.[0] * 
	{ 
		"enabled": true,
		"jsonData": {"onCallApiUrl": "http://oncall-dev-engine:8080", "stackId": 5, "orgId": 100},
		"secureJsonData": { "apiKey": $APIKEY, "grafanaToken": $APIKEY, "onCallApiToken": $ONCALLTOKEN }
	}' .settings >| .settings-merged
	
curl -s -X POST \
        -H "Content-Type: application/json" \
        -d @.settings-merged \
        ${BASE_URL}/api/plugins/grafana-oncall-app/settings | jq -r ".message"

# Print the updated settings for debugging
# curl -s -X GET \
# 	-H "Accept: application/json" \
#   ${BASE_URL}/api/plugins/grafana-oncall-app/settings | jq

rm .settings .settings-merged
