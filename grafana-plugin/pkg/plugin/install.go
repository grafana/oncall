package plugin

import (
	"bytes"
	"encoding/json"
	"github.com/grafana/grafana-plugin-sdk-go/backend/log"
	"io"
	"net/url"

	"net/http"
)

type OnCallInstall struct {
	OnCallError `json:"onCallError,omitempty"`
}

// TODO: Lock so that multiple installs do not revoke each others tokens
func (a *App) handleInstall(w http.ResponseWriter, req *http.Request) {
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

	installURL, err := url.JoinPath(onCallPluginSettings.OnCallAPIURL, "api/internal/v1/plugin/v2/install")
	if err != nil {
		log.DefaultLogger.Error("Error joining path: %v", err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	parsedInstallURL, err := url.Parse(installURL)
	if err != nil {
		log.DefaultLogger.Error("Error parsing path: %v", err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	installReq, err := http.NewRequest("POST", parsedInstallURL.String(), bytes.NewBuffer(onCallSyncJsonData))
	if err != nil {
		log.DefaultLogger.Error("Error creating request: ", err)
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	installReq.Header.Set("Content-Type", "application/json")

	res, err := a.httpClient.Do(installReq)
	if err != nil {
		log.DefaultLogger.Error("Error request to oncall: ", err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer res.Body.Close()

	if res.StatusCode != http.StatusOK {
		w.Header().Add("Content-Type", "application/json")
		installError := OnCallInstall{
			OnCallError: OnCallError{
				Code:    INSTALL_ERROR_CODE,
				Message: "Install failed check /status for details",
			},
		}
		if err := json.NewEncoder(w).Encode(installError); err != nil {
			http.Error(w, "Failed to encode response", http.StatusInternalServerError)
			return
		}
		w.WriteHeader(http.StatusBadRequest)
	} else {
		provisionBody, err := io.ReadAll(res.Body)
		if err != nil {
			log.DefaultLogger.Error("Error reading response body: ", err)
			return
		}

		var provisioningData OnCallProvisioningJSONData
		err = json.Unmarshal(provisionBody, &provisioningData)
		if err != nil {
			log.DefaultLogger.Error("Error unmarshalling OnCallProvisioningJSONData: ", err)
			return
		}

		onCallPluginSettings.OnCallToken = provisioningData.OnCallToken
		err = a.SaveOnCallSettings(onCallPluginSettings)
		if err != nil {
			log.DefaultLogger.Error("Error saving settings: ", err)
			return
		}
		w.WriteHeader(http.StatusOK)
	}

}
