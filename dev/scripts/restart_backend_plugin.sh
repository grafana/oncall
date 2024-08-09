#!/bin/bash

# Find a grafana pod
pod=$(kubectl get pods -l app.kubernetes.io/name=grafana -o=jsonpath='{.items[0].metadata.name}')

if [ -z "$pod" ]; then
    echo "No pod found with the specified label."
    exit 1
fi

# Exec into the pod
kubectl exec -it "$pod" -- /bin/bash <<'EOF'

# Find and kill the process containing "gpx_grafana" (plugin backend process)
process_id=$(ps aux | grep gpx_grafana | grep -v grep | awk '{print $1}')
echo $process_id
if [ -n "$process_id" ]; then
    echo "Killing process $process_id"
    kill $process_id
else
    echo "No process containing 'gpx_grafana' in COMMAND found."
fi
EOF
