# How to run the chart locally

1. Create the cluster with [kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation)

   > Make sure ports 30001 and 30002 are free on your machine

   ```bash
   kind create cluster --image kindest/node:v1.24.7 --config kind.yml
   ```

2. (Optional) Build oncall image locally and load it to kind cluster

3. ```bash
   docker build ../engine -t oncall/engine:latest --target dev
   kind load docker-image oncall/engine:latest
   ```

4. Install the helm chart

   ```bash
      helm install helm-testing \
      --wait \
      --values ./simple.yml \
      ./oncall
   ```

5. Get credentials

   ```bash
   echo "\n\nOpen Grafana on localhost:30002 with credentials - user: admin, password: $(kubectl get secret --namespace default helm-testing-grafana -o jsonpath="{.data.admin-password}" | base64 --decode ; echo)"
   echo "Open Plugins -> Grafana OnCall -> fill form: backend url: http://host.docker.internal:30001"
   ```

6. Clean up

   ```bash
   kind delete cluster
   ```
