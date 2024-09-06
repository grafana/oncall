package plugin

import (
	"encoding/json"
	"net/http"

	"github.com/grafana/grafana-plugin-sdk-go/backend/log"
	"github.com/grafana/grafana-plugin-sdk-go/backend/resource/httpadapter"
)

type OnCallDebugStats struct {
	SettingsCallCount           int32 `json:"settingsCallCount"`
	AllUsersCallCount           int32 `json:"allUsersCallCount"`
	PermissionsCallCount        int32 `json:"permissionsCallCount"`
	AllPermissionsCallCount     int32 `json:"allPermissionsCallCount"`
	TeamForUserCallCount        int32 `json:"teamForUserCallCount"`
	AllTeamsCallCount           int32 `json:"allTeamsCallCount"`
	TeamMembersForTeamCallCount int32 `json:"teamMembersForTeamCallCount"`
	CheckHealthCallCount        int32 `json:"checkHealthCallCount"`
}

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

	onCallSync, err := a.GetSyncData(onCallPluginSettings)
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

func (a *App) handleDebugPermissions(w http.ResponseWriter, req *http.Request) {
	pluginContext := httpadapter.PluginConfigFromContext(req.Context())

	w.Header().Add("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(pluginContext); err != nil {
		http.Error(w, "Failed to encode response", http.StatusInternalServerError)
		return
	}
	w.WriteHeader(http.StatusOK)
}

func (a *App) handleDebugStats(w http.ResponseWriter, req *http.Request) {
	w.Header().Add("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(a.OnCallDebugStats); err != nil {
		http.Error(w, "Failed to encode response", http.StatusInternalServerError)
		return
	}
	w.WriteHeader(http.StatusOK)
}

func (a *App) handleDebugUnlock(w http.ResponseWriter, req *http.Request) {
	a.OnCallSyncCache.syncMutex.Unlock()
	w.WriteHeader(http.StatusOK)
}
