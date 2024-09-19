package plugin

import (
	"bytes"
	"encoding/json"
	"net/http"
	"sort"

	"github.com/grafana/grafana-plugin-sdk-go/backend/log"
)

type OnCallSync struct {
	Users       []OnCallUser         `json:"users"`
	Teams       []OnCallTeam         `json:"teams"`
	TeamMembers map[int][]int        `json:"team_members"`
	Settings    OnCallPluginSettings `json:"settings"`
}

func (a *OnCallSync) Equal(b *OnCallSync) bool {
	if len(a.Users) != len(b.Users) || len(a.Teams) != len(b.Teams) || len(a.TeamMembers) != len(b.TeamMembers) {
		return false
	}
	for i := range a.Users {
		if !a.Users[i].Equal(&b.Users[i]) {
			return false
		}
	}
	for i := range a.Teams {
		if !a.Teams[i].Equal(&b.Teams[i]) {
			return false
		}
	}
	for key, teamMembersA := range a.TeamMembers {
		if teamMembersB, exists := b.TeamMembers[key]; !exists {
			if len(teamMembersA) != len(teamMembersB) {
				return false
			}
			sort.Slice(teamMembersA, func(i, j int) bool {
				return teamMembersA[i] < teamMembersA[j]
			})
			sort.Slice(teamMembersB, func(i, j int) bool {
				return teamMembersB[i] < teamMembersB[j]
			})
			for i := range teamMembersA {
				if teamMembersA[i] != teamMembersB[i] {
					return false
				}
			}
		}
	}
	if !a.Settings.Equal(&b.Settings) {
		return false
	}
	return true
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

func (a *App) HandleInternalApi(w http.ResponseWriter, req *http.Request) {
	a.ProxyRequestToOnCall(w, req, "api/internal/v1/")
}

func (a *App) handleLegacyInstall(w *responseWriter, req *http.Request) {
	var provisioningData OnCallProvisioningJSONData
	err := json.Unmarshal(w.body.Bytes(), &provisioningData)
	if err != nil {
		log.DefaultLogger.Error("Error unmarshalling OnCallProvisioningJSONData", "error", err)
		return
	}

	onCallPluginSettings, err := a.OnCallSettingsFromContext(req.Context())
	if err != nil {
		log.DefaultLogger.Error("Error getting settings from context", "error", err)
		return
	}

	if provisioningData.Error != "" {
		log.DefaultLogger.Error("Error installing OnCall", "error", provisioningData.Error)
		return
	}
	onCallPluginSettings.License = provisioningData.License
	onCallPluginSettings.OrgID = provisioningData.OrgId
	onCallPluginSettings.StackID = provisioningData.StackId
	onCallPluginSettings.OnCallToken = provisioningData.OnCallToken

	err = a.SaveOnCallSettings(onCallPluginSettings)
	if err != nil {
		log.DefaultLogger.Error("Error saving settings", "error", err)
		return
	}
}

// registerRoutes takes a *http.ServeMux and registers some HTTP handlers.
func (a *App) registerRoutes(mux *http.ServeMux) {
	mux.HandleFunc("/plugin/install", a.handleInstall)
	mux.HandleFunc("/plugin/status", a.HandleStatus)
	mux.HandleFunc("/plugin/sync", a.HandleSync)

	mux.Handle("/plugin/self-hosted/install", afterRequest(http.HandlerFunc(a.HandleInternalApi), a.handleLegacyInstall))

	// Disable debug endpoints
	//mux.HandleFunc("/debug/user", a.handleDebugUser)
	//mux.HandleFunc("/debug/sync", a.handleDebugSync)
	//mux.HandleFunc("/debug/settings", a.handleDebugSettings)
	//mux.HandleFunc("/debug/permissions", a.handleDebugPermissions)
	//mux.HandleFunc("/debug/stats", a.handleDebugStats)
	//mux.HandleFunc("/debug/unlock", a.handleDebugUnlock)

	mux.HandleFunc("/", a.HandleInternalApi)
}
