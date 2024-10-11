package plugin

import (
	"bytes"
	"encoding/json"
	"io"
	"net/url"

	"github.com/grafana/grafana-plugin-sdk-go/backend/log"

	"net/http"
)

type OnCallInstall struct {
	OnCallError `json:"onCallError,omitempty"`
}

func (a *App) handleInstall(w http.ResponseWriter, req *http.Request) {
	if req.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	locked := a.installMutex.TryLock()
	if !locked {
		http.Error(w, "Install is already in progress", http.StatusBadRequest)
		return
	}
	defer a.installMutex.Unlock()

	onCallPluginSettings, err := a.OnCallSettingsFromContext(req.Context())
	if err != nil {
		log.DefaultLogger.Error("Error getting settings from context", "error", err)
		return
	}

	healthStatus, err := a.CheckOnCallApiHealthStatus(onCallPluginSettings)
	if err != nil {
		log.DefaultLogger.Error("Error checking on-call API health", "error", err)
		http.Error(w, err.Error(), healthStatus)
		return
	}

	onCallSync, err := a.GetSyncData(onCallPluginSettings)
	if err != nil {
		log.DefaultLogger.Error("Error getting sync data", "error", err)
		return
	}

	onCallSyncJsonData, err := json.Marshal(onCallSync)
	if err != nil {
		log.DefaultLogger.Error("Error marshalling JSON", "error", err)
		return
	}

	installURL, err := url.JoinPath(onCallPluginSettings.OnCallAPIURL, "api/internal/v1/plugin/v2/install")
	if err != nil {
		log.DefaultLogger.Error("Error joining path", "error", err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	parsedInstallURL, err := url.Parse(installURL)
	if err != nil {
		log.DefaultLogger.Error("Error parsing path", "error", err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	installReq, err := http.NewRequest("POST", parsedInstallURL.String(), bytes.NewBuffer(onCallSyncJsonData))
	if err != nil {
		log.DefaultLogger.Error("Error creating request", "error", err)
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	installReq.Header.Set("Content-Type", "application/json")

	res, err := a.httpClient.Do(installReq)
	if err != nil {
		log.DefaultLogger.Error("Error request to oncall", "error", err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer res.Body.Close()

	if res.StatusCode != http.StatusOK {
		errorBody, err := io.ReadAll(res.Body)
		var installError = OnCallInstall{
			OnCallError: OnCallError{
				Code:    INSTALL_ERROR_CODE,
				Message: "Install failed check /status for details",
			},
		}
		if errorBody != nil {
			var tempError OnCallError
			err = json.Unmarshal(errorBody, &tempError)
			if err != nil {
				log.DefaultLogger.Error("Error unmarshalling OnCallError", "error", err)
			}
			if tempError.Message == "" {
				installError.OnCallError.Message = string(errorBody)
			} else {
				installError.OnCallError = tempError
			}
		}

		w.Header().Add("Content-Type", "application/json")
		if err := json.NewEncoder(w).Encode(installError); err != nil {
			http.Error(w, "Failed to encode response", http.StatusInternalServerError)
			return
		}
		w.WriteHeader(http.StatusBadRequest)
	} else {
		provisionBody, err := io.ReadAll(res.Body)
		if err != nil {
			log.DefaultLogger.Error("Error reading response body", "error", err)
			return
		}

		var provisioningData OnCallProvisioningJSONData
		err = json.Unmarshal(provisionBody, &provisioningData)
		if err != nil {
			log.DefaultLogger.Error("Error unmarshalling OnCallProvisioningJSONData", "error", err)
			return
		}

		onCallPluginSettings.OnCallToken = provisioningData.OnCallToken
		err = a.SaveOnCallSettings(onCallPluginSettings)
		if err != nil {
			log.DefaultLogger.Error("Error saving settings", "error", err)
			return
		}
		w.WriteHeader(http.StatusOK)
	}

}
