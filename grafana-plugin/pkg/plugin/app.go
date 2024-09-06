package plugin

import (
	"context"
	"fmt"
	"net/http"
	"net/url"
	"sync"
	"sync/atomic"
	"time"

	"github.com/grafana/grafana-plugin-sdk-go/backend"
	"github.com/grafana/grafana-plugin-sdk-go/backend/httpclient"
	"github.com/grafana/grafana-plugin-sdk-go/backend/instancemgmt"
	"github.com/grafana/grafana-plugin-sdk-go/backend/log"
	"github.com/grafana/grafana-plugin-sdk-go/backend/resource/httpadapter"
)

// Make sure App implements required interfaces. This is important to do
// since otherwise we will only get a not implemented error response from plugin in
// runtime. Plugin should not implement all these interfaces - only those which are
// required for a particular task.
var (
	_ backend.CallResourceHandler   = (*App)(nil)
	_ instancemgmt.InstanceDisposer = (*App)(nil)
	_ backend.CheckHealthHandler    = (*App)(nil)
)

// App is an example app backend plugin which can respond to data queries.
type App struct {
	backend.CallResourceHandler
	httpClient   *http.Client
	installMutex sync.Mutex
	*OnCallSyncCache
	*OnCallSettingsCache
	*OnCallUserCache
	*OnCallDebugStats
}

// NewApp creates a new example *App instance.
func NewApp(ctx context.Context, settings backend.AppInstanceSettings) (*App, error) {
	var app App

	app.OnCallSyncCache = &OnCallSyncCache{}
	app.OnCallSettingsCache = &OnCallSettingsCache{}
	app.OnCallUserCache = NewOnCallUserCache()
	app.OnCallDebugStats = &OnCallDebugStats{}

	opts, err := settings.HTTPClientOptions(ctx)
	if err != nil {
		return nil, fmt.Errorf("http client options: %w", err)
	}

	cl, err := httpclient.New(opts)
	if err != nil {
		return nil, fmt.Errorf("httpclient new: %w", err)
	}
	app.httpClient = cl

	return &app, nil
}

// NewInstance creates a new example *Instance instance.
func NewInstance(ctx context.Context, settings backend.AppInstanceSettings) (instancemgmt.Instance, error) {
	app, err := NewApp(ctx, settings)

	if err != nil {
		log.DefaultLogger.Error("Error creating new app", "error", err)
		return nil, err
	}

	// Use a httpadapter (provided by the SDK) for resource calls. This allows us
	// to use a *http.ServeMux for resource calls, so we can map multiple routes
	// to CallResource without having to implement extra logic.
	mux := http.NewServeMux()
	app.registerRoutes(mux)
	app.CallResourceHandler = httpadapter.New(mux)

	return app, nil
}

// Dispose here tells plugin SDK that plugin wants to clean up resources when a new instance
// created.
func (a *App) Dispose() {
	// cleanup
}

// CheckHealth handles health checks sent from Grafana to the plugin.
func (a *App) CheckHealth(_ context.Context, _ *backend.CheckHealthRequest) (*backend.CheckHealthResult, error) {
	log.DefaultLogger.Info("CheckHealth")
	return &backend.CheckHealthResult{
		Status:  backend.HealthStatusOk,
		Message: "ok",
	}, nil
}

// Check OnCallApi health
func (a *App) CheckOnCallApiHealthStatus(onCallPluginSettings *OnCallPluginSettings) (int, error) {
	atomic.AddInt32(&a.CheckHealthCallCount, 1)
	healthURL, err := url.JoinPath(onCallPluginSettings.OnCallAPIURL, "/api/internal/v1/health/")
	if err != nil {
		log.DefaultLogger.Error("Error joining path", "error", err)
		return http.StatusInternalServerError, err
	}

	parsedHealthURL, err := url.Parse(healthURL)
	if err != nil {
		log.DefaultLogger.Error("Error parsing path", "error", err)
		return http.StatusInternalServerError, err
	}

	healthReq, err := http.NewRequest("GET", parsedHealthURL.String(), nil)
	if err != nil {
		log.DefaultLogger.Error("Error creating request", "error", err)
		return http.StatusBadRequest, err
	}

	client := &http.Client{
		Timeout: 500 * time.Millisecond,
	}
	healthRes, err := client.Do(healthReq)
	if err != nil {
		log.DefaultLogger.Error("Error request to oncall", "error", err)
		return http.StatusBadRequest, err
	}

	if healthRes.StatusCode != http.StatusOK {
		log.DefaultLogger.Error("Error request to oncall", "error", healthRes.Status)
		return healthRes.StatusCode, fmt.Errorf(healthRes.Status)
	}

	return http.StatusOK, nil
}
