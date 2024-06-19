package plugin

import (
	"bytes"
	"encoding/json"
	"fmt"
	"github.com/grafana/grafana-plugin-sdk-go/backend/log"
	"net/http"
)

type OnCallSync struct {
	Users       []OnCallUser         `json:"users"`
	Teams       []OnCallTeam         `json:"teams"`
	TeamMembers map[int][]int        `json:"team_members"`
	Settings    OnCallPluginSettings `json:"settings"`
}

type responseWriter struct {
	http.ResponseWriter
	statusCode int
	body       bytes.Buffer
}

func (rw *responseWriter) WriteHeader(statusCode int) {
	rw.statusCode = statusCode
	rw.ResponseWriter.WriteHeader(statusCode)
}

func (rw *responseWriter) Write(b []byte) (int, error) {
	if rw.statusCode == 0 {
		rw.WriteHeader(http.StatusOK)
	}
	n, err := rw.body.Write(b)
	if err != nil {
		return n, err
	}
	return rw.ResponseWriter.Write(b)
}

func afterRequest(handler http.Handler, afterFunc func(*responseWriter, *http.Request)) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		wrappedWriter := &responseWriter{ResponseWriter: w}
		handler.ServeHTTP(wrappedWriter, r)
		afterFunc(wrappedWriter, r)
	})
}

func (a *App) handleInternalApi(w http.ResponseWriter, req *http.Request) {
	a.ProxyRequestToOnCall(w, req, "api/internal/v1/")
}

func (a *App) handleLegacyInstall(w *responseWriter, req *http.Request) {
	var provisioningData OnCallProvisioningJSONData
	err := json.Unmarshal(w.body.Bytes(), &provisioningData)
	if err != nil {
		log.DefaultLogger.Error("Error unmarshalling OnCallProvisioningJSONData: ", err)
		return
	}

	onCallPluginSettings, err := a.OnCallSettingsFromContext(req.Context())
	if err != nil {
		log.DefaultLogger.Error("Error getting settings from context: ", err)
		return
	}

	log.DefaultLogger.Info(fmt.Sprintf("Settings = %+v", onCallPluginSettings))
	log.DefaultLogger.Info(fmt.Sprintf("Provisioning data = %+v", provisioningData))

	if provisioningData.Error != "" {
		log.DefaultLogger.Error(fmt.Sprintf("Error installing OnCall = %s", provisioningData.Error))
		return
	}
	onCallPluginSettings.License = provisioningData.License
	onCallPluginSettings.OrgID = provisioningData.OrgId
	onCallPluginSettings.StackID = provisioningData.StackId
	onCallPluginSettings.OnCallToken = provisioningData.OnCallToken

	err = a.SaveOnCallSettings(onCallPluginSettings)
	if err != nil {
		log.DefaultLogger.Error("Error saving settings: ", err)
		return
	}
}

// registerRoutes takes a *http.ServeMux and registers some HTTP handlers.
func (a *App) registerRoutes(mux *http.ServeMux) {
	mux.HandleFunc("/plugin/install", a.handleInstall)
	mux.HandleFunc("/plugin/status", a.handleStatus)

	mux.Handle("/plugin/self-hosted/install", afterRequest(http.HandlerFunc(a.handleInternalApi), a.handleLegacyInstall))

	mux.HandleFunc("/debug/user", a.handleDebugUser)
	mux.HandleFunc("/debug/sync", a.handleDebugSync)
	mux.HandleFunc("/debug/settings", a.handleDebugSettings)

	mux.HandleFunc("/", a.handleInternalApi)
}
