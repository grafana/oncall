# How to run the chart locally

1. Create the cluster with [kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation)

   > Make sure ports 30001 and 30002 are free on your machine

   ```
   kind create cluster --image kindest/node:v1.24.7 --config kind.yml
   ```

2. Install the helm chart

   ```
   helm install helm-testing \
   ../oncall --wait --timeout 30m \
   --wait-for-jobs \
   --values ci/simple.yml \
   --values ci/values-arm64.yml
   ```

3. Get credentials

   ```
   echo "\n\nOpen Grafana on localhost:30002 with credentials - user: admin, password: $(kubectl get secret --namespace default helm-testing-grafana -o jsonpath="{.data.admin-password}" | base64 --decode ; echo)"
   echo "Open Plugins -> Grafana OnCall -> fill form: backend url: localhost:30001, grafana url: localhost: 30001, token below"
   export POD_NAME=$(kubectl get pods --namespace default -l "app.kubernetes.io/name=oncall,app.kubernetes.io/instance=helm-testing,app.kubernetes.io/component=engine" -o jsonpath="{.items[0].metadata.name}")
   ```

4. Clean up
   ```
   kind delete cluster
   ```
