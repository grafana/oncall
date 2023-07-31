# Grafana OnCall Terraform Plugin

Use the Grafana Terraform provider to manage OnCall resources, such as schedules, escalation chains and
more within your “as-code” workflow.

To learn more:

* read our [Get started with Grafana OnCall and Terraform](
<https://grafana.com/blog/2022/08/29/get-started-with-grafana-oncall-and-terraform/>) blog post
* refer to the [Terraform provider documentation](https://registry.terraform.io/providers/grafana/oncall/latest/docs)
* check out the [Terraform provider source code](https://github.com/grafana/terraform-provider-grafana)

## How to build OnCall Terraform plugin locally (developer notes)

> Refer to [Terraform provider README.md](https://github.com/grafana/terraform-provider-grafana/blob/master/README.md)
for more details.

1. Clone [Grafana OnCall Go Client repo](https://github.com/grafana/amixr-api-go-client/) and make local changes
1. Clone [Grafana Terraform plugin repo](https://github.com/grafana/terraform-provider-grafana),
check [Readme](https://github.com/grafana/terraform-provider-grafana/blob/master/README.md) and make local changes
1. Set env variables
  
    > Warning: you might want to set another OS_ARCH, provided value are for Apple Silicon

    ```bash
    export BINARY=terraform-provider-grafana
    OS_ARCH=darwin_arm64
    HOSTNAME=grafana.com
    NAMESPACE=raintank
    NAME=grafana
    VERSION=1.0.0
    ```

1. Build provider

    ```bash
    go build -o ${BINARY}
    ```

1. If there are changes to `grafana/amixr-api-go-client/` make sure to replace it in provider's go.mod:

    > Warning: this command is example, name or version of api client might and will change, check provider's go.mod

    ```go
    // TODO: remove this after testing
    replace github.com/grafana/amixr-api-go-client v0.0.8 => /YOUR_LOCAL_PATH/amixr-api-go-client
    ```

1. Create a `.terraformrc` in `$HOME` directory and paste the following

    ```yaml
    provider_installation {
      dev_overrides {
          "grafana/grafana" = "/path/to/your/grafana/terraform-provider" # this path is the directory where the binary is built
      }
   }
    ```

1. Create a new directory and a `main.tf` file with the following content:

    ```terraform
    terraform {
      required_providers {
        grafana = {
          source  = "grafana/grafana"
          version = "1.0.0"
        }
      }
    }

    provider "grafana" {
      alias = "oncall"
      oncall_access_token = 
      oncall_url          =  
    }
    ```

1. Run the following commands to initialize Terraform and apply the configuration:

    ```bash
    terrafrom init
    terraform plan/apply
    ```
