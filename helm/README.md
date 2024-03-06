# How to run the chart locally

1. Create the cluster with [kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation)

   > Make sure ports 30001, 30002 (Grafana, optional) and
   > 30003 (detached integrations server, optional) are free on your machine

   ```bash
   kind create cluster --image kindest/node:v1.24.7 --config kind.yml
   ```

2. (Optional) Build oncall image locally and load it to kind cluster

   ```bash
      docker build ../engine -t oncall/engine:latest --target dev
      kind load docker-image oncall/engine:latest
   ```

   Also make sure to add the following lines to your `simple.yml` (you may also need to enable `devMode`):

   ```yaml
   image:
     repository: oncall/engine
     tag: latest
     pullPolicy: IfNotPresent
   oncall:
     devMode: true
   ```

   Alternatively you can also pass an extra `--values ./local_image.yml` in the command below.

3. Install the helm chart

   ```bash
      helm install helm-testing \
      --wait \
      --values ./simple.yml \
      ./oncall
   ```

4. Get credentials

   ```bash
   echo "\n\nOpen Grafana on localhost:30002 with credentials - user: admin, password: $(kubectl get secret --namespace default helm-testing-grafana -o jsonpath="{.data.admin-password}" | base64 --decode ; echo)"
   echo "Open Plugins -> Grafana OnCall -> fill form: backend url: http://host.docker.internal:30001"
   ```

5. Clean up
   If you happen to `helm uninstall helm-testing` be sure to delete all the Persistent Volume Claims, as Postgres stores
   the auto-generated password on disk, and the next `helm install` will fail.

   ```bash
   kubectl delete pvc --all
   kubectl delete pv --all
   ```

   This, of course, will delete all the PVs and PVCs also :-)

   ```bash
   kind delete cluster
   ```
