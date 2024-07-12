package plugin

import (
	"encoding/json"
	"github.com/grafana/grafana-plugin-sdk-go/backend/log"
	"github.com/grafana/grafana-plugin-sdk-go/backend/resource/httpadapter"
	"net/http"
)

func (a *App) handleDebugUser(w http.ResponseWriter, req *http.Request) {
	onCallPluginSettings, err := a.OnCallSettingsFromContext(req.Context())
	if err != nil {
		log.DefaultLogger.Error("Error getting settings from context", "error", err)
		return
	}

	user := httpadapter.UserFromContext(req.Context())
	onCallUser, err := a.GetUserForHeader(onCallPluginSettings, user)
	if err != nil {
		log.DefaultLogger.Error("Error getting user", "error", err)
		return
	}

	w.Header().Add("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(onCallUser); err != nil {
		http.Error(w, "Failed to encode response", http.StatusInternalServerError)
		return
	}
	w.WriteHeader(http.StatusOK)
}

func (a *App) handleDebugSync(w http.ResponseWriter, req *http.Request) {
	onCallPluginSettings, err := a.OnCallSettingsFromContext(req.Context())
	if err != nil {
		log.DefaultLogger.Error("Error getting settings from context", "error", err)
		return
	}

	onCallSync, err := a.GetSyncData(req.Context(), onCallPluginSettings)
	if err != nil {
		log.DefaultLogger.Error("Error getting sync data", "error", err)
		return
	}

	w.Header().Add("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(onCallSync); err != nil {
		http.Error(w, "Failed to encode response", http.StatusInternalServerError)
		return
	}
	w.WriteHeader(http.StatusOK)
}

func (a *App) handleDebugSettings(w http.ResponseWriter, req *http.Request) {
	onCallPluginSettings, err := a.OnCallSettingsFromContext(req.Context())
	if err != nil {
		log.DefaultLogger.Error("Error getting settings from context", "error", err)
		return
	}

	w.Header().Add("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(onCallPluginSettings); err != nil {
		http.Error(w, "Failed to encode response", http.StatusInternalServerError)
		return
	}
	w.WriteHeader(http.StatusOK)
}
