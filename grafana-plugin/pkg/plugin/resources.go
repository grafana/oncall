package plugin

import (
	"bytes"
	"encoding/json"
	"fmt"
	"github.com/grafana/grafana-plugin-sdk-go/backend/log"
	"github.com/grafana/grafana-plugin-sdk-go/backend/resource/httpadapter"
	"net/http"
)

type OnCallFeaturesConfig struct {
	RBACEnabled        bool   `json:"rbac_enabled"`
	IncidentEnabled    bool   `json:"incident_enabled"`
	IncidentBackendURL string `json:"incident_backend_url,omitempty"`
	LabelsEnabled      bool   `json:"labels_enabled"`
}

type OnCallSync struct {
	Users       []OnCallUser         `json:"users"`
	Teams       []OnCallTeam         `json:"teams"`
	TeamMembers map[int][]int        `json:"team_members"`
	Config      OnCallFeaturesConfig `json:"config"`
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

func (a *App) handleInstall(w *responseWriter, req *http.Request) {
	var provisioningData OnCallProvisioningJSONData
	err := json.Unmarshal(w.body.Bytes(), &provisioningData)
	if err != nil {
		log.DefaultLogger.Error(fmt.Sprintf("Error unmarshalling OnCallProvisioningJSONData = %+v", err))
		return
	}

	onCallPluginSettings, err := a.OnCallSettingsFromContext(req.Context())
	if err != nil {
		log.DefaultLogger.Error(fmt.Sprintf("Error getting settings from context = %+v", err))
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
		log.DefaultLogger.Error(fmt.Sprintf("Error saving settings = %+v", err))
		return
	}
}

func (a *App) handleCurrentUser(w http.ResponseWriter, req *http.Request) {
	onCallPluginSettings, err := a.OnCallSettingsFromContext(req.Context())
	if err != nil {
		log.DefaultLogger.Error(fmt.Sprintf("Error getting settings from context = %+v", err))
		return
	}

	user := httpadapter.UserFromContext(req.Context())
	onCallUser, err := a.GetUserForHeader(&onCallPluginSettings, user)
	if err != nil {
		log.DefaultLogger.Error(fmt.Sprintf("Error getting user = %+v", err))
		return
	}

	w.Header().Add("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(onCallUser); err != nil {
		http.Error(w, "Failed to encode response", http.StatusInternalServerError)
		return
	}
	w.WriteHeader(http.StatusOK)
}

func (a *App) handleSync(w http.ResponseWriter, req *http.Request) {
	onCallPluginSettings, err := a.OnCallSettingsFromContext(req.Context())
	if err != nil {
		log.DefaultLogger.Error(fmt.Sprintf("Error getting settings from context = %+v", err))
		return
	}

	onCallSync, err := a.GetSyncData(req.Context(), &onCallPluginSettings)
	if err != nil {
		log.DefaultLogger.Error(fmt.Sprintf("Error getting sync data = %+v", err))
		return
	}

	w.Header().Add("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(onCallSync); err != nil {
		http.Error(w, "Failed to encode response", http.StatusInternalServerError)
		return
	}
	w.WriteHeader(http.StatusOK)
}

// registerRoutes takes a *http.ServeMux and registers some HTTP handlers.
func (a *App) registerRoutes(mux *http.ServeMux) {
	mux.Handle("/plugin/self-hosted/install", afterRequest(http.HandlerFunc(a.handleInternalApi), a.handleInstall))
	mux.HandleFunc("/test-current-user", a.handleCurrentUser)
	mux.HandleFunc("/test-sync", a.handleSync)
	mux.HandleFunc("/", a.handleInternalApi)
}
