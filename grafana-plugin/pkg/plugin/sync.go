package plugin

import (
	"bytes"
	"encoding/json"
	"net/url"

	"github.com/grafana/grafana-plugin-sdk-go/backend/log"

	"net/http"
)

func (a *App) handleSync(w http.ResponseWriter, req *http.Request) {
	onCallPluginSettings, err := a.OnCallSettingsFromContext(req.Context())
	if err != nil {
		log.DefaultLogger.Error("Error getting settings from context: ", err)
		return
	}

	onCallSync, err := a.GetSyncData(req.Context(), onCallPluginSettings)
	if err != nil {
		log.DefaultLogger.Error("Error getting sync data: ", err)
		return
	}

	onCallSyncJsonData, err := json.Marshal(onCallSync)
	if err != nil {
		log.DefaultLogger.Error("Error marshalling JSON: ", err)
		return
	}

	syncURL, err := url.JoinPath(onCallPluginSettings.OnCallAPIURL, "api/internal/v1/plugin/v2/sync")
	if err != nil {
		log.DefaultLogger.Error("Error joining path: %v", err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	parsedSyncURL, err := url.Parse(syncURL)
	if err != nil {
		log.DefaultLogger.Error("Error parsing path: %v", err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	syncReq, err := http.NewRequest("POST", parsedSyncURL.String(), bytes.NewBuffer(onCallSyncJsonData))
	if err != nil {
		log.DefaultLogger.Error("Error creating request: ", err)
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	err = a.SetupRequestHeadersForOnCall(req.Context(), onCallPluginSettings, syncReq)
	if err != nil {
		log.DefaultLogger.Error("Error setting up headers: %v", err)
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	syncReq.Header.Set("Content-Type", "application/json")

	res, err := a.httpClient.Do(syncReq)
	if err != nil {
		log.DefaultLogger.Error("Error request to oncall: ", err)
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	defer res.Body.Close()

	w.WriteHeader(http.StatusOK)
}
