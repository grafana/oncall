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

func (a *App) InstallOnCallFromPluginSettings(pluginSettings *OnCallPluginSettings, persistPluginSettingsToGrafana bool) (*OnCallProvisioningJSONData, int, *OnCallInstall, error) {
	var provisioningData OnCallProvisioningJSONData

	healthStatus, err := a.CheckOnCallApiHealthStatus(pluginSettings)
	if err != nil {
		log.DefaultLogger.Error("Error checking on-call API health", "error", err)
		return nil, healthStatus, nil, err
	}

	onCallSync, err := a.GetSyncData(pluginSettings)
	if err != nil {
		log.DefaultLogger.Error("Error getting sync data", "error", err)
		return nil, http.StatusInternalServerError, nil, err
	}

	onCallSyncJsonData, err := json.Marshal(onCallSync)
	if err != nil {
		log.DefaultLogger.Error("Error marshalling JSON", "error", err)
		return nil, http.StatusInternalServerError, nil, err
	}

	installURL, err := url.JoinPath(pluginSettings.OnCallAPIURL, "api/internal/v1/plugin/v2/install")
	if err != nil {
		log.DefaultLogger.Error("Error joining path", "error", err)
		return nil, http.StatusInternalServerError, nil, err
	}

	parsedInstallURL, err := url.Parse(installURL)
	if err != nil {
		log.DefaultLogger.Error("Error parsing path", "error", err)
		return nil, http.StatusInternalServerError, nil, err
	}

	installReq, err := http.NewRequest("POST", parsedInstallURL.String(), bytes.NewBuffer(onCallSyncJsonData))
	if err != nil {
		log.DefaultLogger.Error("Error creating request", "error", err)
		return nil, http.StatusBadRequest, nil, err
	}
	installReq.Header.Set("Content-Type", "application/json")

	res, err := a.httpClient.Do(installReq)
	if err != nil {
		log.DefaultLogger.Error("Error request to oncall", "error", err)
		return nil, http.StatusInternalServerError, nil, err
	}
	defer res.Body.Close()

	if res.StatusCode != http.StatusOK {
		errorBody, _ := io.ReadAll(res.Body)
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

		return nil, http.StatusBadRequest, &installError, nil
	} else {
		provisionBody, err := io.ReadAll(res.Body)
		if err != nil {
			log.DefaultLogger.Error("Error reading response body", "error", err)
			return nil, http.StatusInternalServerError, nil, err
		}

		err = json.Unmarshal(provisionBody, &provisioningData)
		if err != nil {
			log.DefaultLogger.Error("Error unmarshalling OnCallProvisioningJSONData", "error", err)
			return nil, http.StatusInternalServerError, nil, err
		}

		if persistPluginSettingsToGrafana {
			pluginSettings.OnCallToken = provisioningData.OnCallToken

			if err = a.SaveOnCallSettings(pluginSettings); err != nil {
				log.DefaultLogger.Error("Error saving settings", "error", err)
				return nil, http.StatusInternalServerError, nil, err
			}
		}
	}

	return &provisioningData, http.StatusOK, nil, nil
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

	_, httpStatusCode, installError, err := a.InstallOnCallFromPluginSettings(onCallPluginSettings, true)
	if err != nil {
		log.DefaultLogger.Error("Error installing oncall", "error", err)
		http.Error(w, err.Error(), httpStatusCode)
		return
	} else if installError != nil {
		w.Header().Add("Content-Type", "application/json")
		if err := json.NewEncoder(w).Encode(installError); err != nil {
			log.DefaultLogger.Error("Error encoding response", "error", err)
			http.Error(w, "Failed to encode response", http.StatusInternalServerError)
		}
		w.WriteHeader(httpStatusCode)
		return
	}

	w.WriteHeader(http.StatusOK)
}
