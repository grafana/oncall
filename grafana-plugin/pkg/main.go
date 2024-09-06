package main

import (
	"os"

	"github.com/grafana/grafana-oncall-app/pkg/plugin"
	"github.com/grafana/grafana-plugin-sdk-go/backend/app"
	"github.com/grafana/grafana-plugin-sdk-go/backend/log"
)

func main() {
	// Start listening to requests sent from Grafana. This call is blocking so
	// it won't finish until Grafana shuts down the process or the plugin choose
	// to exit by itself using os.Exit. Manage automatically manages life cycle
	// of app instances. It accepts app instance factory as first
	// argument. This factory will be automatically called on incoming request
	// from Grafana to create different instances of `App` (per plugin
	// ID).
	if err := app.Manage("grafana-oncall-app", plugin.NewInstance, app.ManageOpts{}); err != nil {
		log.DefaultLogger.Error(err.Error())
		os.Exit(1)
	}
}
