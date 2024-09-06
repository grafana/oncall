package plugin

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"

	"github.com/grafana/grafana-plugin-sdk-go/backend/log"
)

type OnCallPluginConnectionEntry struct {
	Ok    bool   `json:"ok"`
	Error string `json:"error,omitempty"`
}

func (e *OnCallPluginConnectionEntry) SetValid() {
	e.Ok = true
	e.Error = ""
}

func (e *OnCallPluginConnectionEntry) SetInvalid(reason string) {
	e.Ok = false
	e.Error = reason
}

func DefaultPluginConnectionEntry() OnCallPluginConnectionEntry {
	return OnCallPluginConnectionEntry{
		Ok:    false,
		Error: "Not validated",
	}
}

type OnCallPluginConnection struct {
	Settings             OnCallPluginConnectionEntry `json:"settings"`
	ServiceAccountToken  OnCallPluginConnectionEntry `json:"service_account_token"`
	GrafanaURLFromPlugin OnCallPluginConnectionEntry `json:"grafana_url_from_plugin"`
	GrafanaURLFromEngine OnCallPluginConnectionEntry `json:"grafana_url_from_engine"`
	OnCallAPIURL         OnCallPluginConnectionEntry `json:"oncall_api_url"`
	OnCallToken          OnCallPluginConnectionEntry `json:"oncall_token"`
}

func DefaultPluginConnection() OnCallPluginConnection {
	return OnCallPluginConnection{
		Settings:             DefaultPluginConnectionEntry(),
		GrafanaURLFromPlugin: DefaultPluginConnectionEntry(),
		ServiceAccountToken:  DefaultPluginConnectionEntry(),
		OnCallAPIURL:         DefaultPluginConnectionEntry(),
		OnCallToken:          DefaultPluginConnectionEntry(),
		GrafanaURLFromEngine: DefaultPluginConnectionEntry(),
	}
}

type OnCallEngineConnection struct {
	GrafanaURL string `json:"url"`
	Connected  bool   `json:"connected"`
	StatusCode int    `json:"status_code"`
	Message    string `json:"message"`
}

type OnCallEngineStatus struct {
	ConnectionToGrafana                   OnCallEngineConnection `json:"connection_to_grafana"`
	License                               string                 `json:"license"`
	Version                               string                 `json:"version"`
	CurrentlyUndergoingMaintenanceMessage string                 `json:"currently_undergoing_maintenance_message"`
	APIURL                                string                 `json:"api_url"`
}

type OnCallStatus struct {
	PluginConnection                      OnCallPluginConnection `json:"pluginConnection,omitempty"`
	License                               string                 `json:"license"`
	Version                               string                 `json:"version"`
	CurrentlyUndergoingMaintenanceMessage string                 `json:"currently_undergoing_maintenance_message"`
	APIURL                                string                 `json:"api_url"`
}

func (s *OnCallStatus) AllOk() bool {
	return s.PluginConnection.Settings.Ok &&
		s.PluginConnection.GrafanaURLFromPlugin.Ok &&
		s.PluginConnection.ServiceAccountToken.Ok &&
		s.PluginConnection.OnCallAPIURL.Ok &&
		s.PluginConnection.OnCallToken.Ok &&
		s.PluginConnection.GrafanaURLFromEngine.Ok
}

func (c *OnCallPluginConnection) ValidateOnCallPluginSettings(settings *OnCallPluginSettings) bool {
	// TODO: Return all instead of first?
	if settings.StackID == 0 {
		c.Settings.SetInvalid("jsonData.stackId is not set")
	} else if settings.OrgID == 0 {
		c.Settings.SetInvalid("jsonData.orgId is not set")
	} else if settings.License == "" {
		c.Settings.SetInvalid("jsonData.license is not set")
	} else if settings.OnCallAPIURL == "" {
		c.Settings.SetInvalid("jsonData.onCallApiUrl is not set")
	} else if settings.GrafanaURL == "" {
		c.Settings.SetInvalid("jsonData.grafanaUrl is not set")
	} else {
		c.Settings.SetValid()
	}
	return c.Settings.Ok
}

func (a *App) ValidateGrafanaConnectionFromPlugin(status *OnCallStatus, settings *OnCallPluginSettings) (bool, error) {
	reqURL, err := url.Parse(settings.GrafanaURL)
	if err != nil {
		status.PluginConnection.GrafanaURLFromPlugin.SetInvalid(fmt.Sprintf("Failed to parse grafana URL %s, %v", settings.GrafanaURL, err))
		return false, nil
	}

	reqURL.Path += "api/org"
	req, err := http.NewRequest("GET", reqURL.String(), nil)
	if err != nil {
		return false, fmt.Errorf("error creating new request: %+v", err)
	}
	req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", settings.GrafanaToken))

	res, err := a.httpClient.Do(req)
	if err != nil {
		return false, fmt.Errorf("error making request: %+v", err)
	}
	defer res.Body.Close()

	if res.StatusCode == http.StatusOK {
		status.PluginConnection.GrafanaURLFromPlugin.SetValid()
		status.PluginConnection.ServiceAccountToken.SetValid()
	} else if res.StatusCode == http.StatusUnauthorized || res.StatusCode == http.StatusForbidden {
		status.PluginConnection.GrafanaURLFromPlugin.SetValid()
		status.PluginConnection.ServiceAccountToken.SetInvalid(fmt.Sprintf("Grafana %s, status code %d", reqURL.String(), res.StatusCode))
	} else {
		status.PluginConnection.GrafanaURLFromPlugin.SetInvalid(fmt.Sprintf("Grafana %s, status code %d", reqURL.String(), res.StatusCode))
	}

	return status.PluginConnection.ServiceAccountToken.Ok && status.PluginConnection.GrafanaURLFromPlugin.Ok, nil
}

func (a *App) ValidateOnCallConnection(ctx context.Context, status *OnCallStatus, settings *OnCallPluginSettings) error {
	healthStatus, err := a.CheckOnCallApiHealthStatus(settings)
	if err != nil {
		log.DefaultLogger.Error("Error checking OnCall API health", "error", err)
		status.PluginConnection.OnCallAPIURL = OnCallPluginConnectionEntry{
			Ok:    false,
			Error: fmt.Sprintf("Error checking OnCall API health. %v. Status code: %d", err, healthStatus),
		}
		return nil
	}

	statusURL, err := url.JoinPath(settings.OnCallAPIURL, "api/internal/v1/plugin/v2/status")
	if err != nil {
		return fmt.Errorf("error joining path: %v", err)
	}

	parsedStatusURL, err := url.Parse(statusURL)
	if err != nil {
		return fmt.Errorf("error parsing path: %v", err)
	}

	statusReq, err := http.NewRequest("GET", parsedStatusURL.String(), nil)
	if err != nil {
		return fmt.Errorf("error creating request: %v", err)
	}

	statusReq.Header.Set("Content-Type", "application/json")
	err = a.SetupRequestHeadersForOnCallWithUser(ctx, settings, statusReq)
	if err != nil {
		return fmt.Errorf("error setting up request headers: %v ", err)
	}

	res, err := a.httpClient.Do(statusReq)
	if err != nil {
		return fmt.Errorf("error request to oncall: %v ", err)
	}
	defer res.Body.Close()

	if res.StatusCode != http.StatusOK {
		if res.StatusCode == http.StatusUnauthorized || res.StatusCode == http.StatusForbidden {
			status.PluginConnection.OnCallToken = OnCallPluginConnectionEntry{
				Ok:    false,
				Error: fmt.Sprintf("Unauthorized/Forbidden while accessing OnCall engine: %s, status code: %d, check token", statusReq.URL.Path, res.StatusCode),
			}
		} else {
			status.PluginConnection.OnCallAPIURL = OnCallPluginConnectionEntry{
				Ok:    false,
				Error: fmt.Sprintf("Unable to connect to OnCall engine: %s, status code: %d", statusReq.URL.Path, res.StatusCode),
			}
		}
	} else {
		status.PluginConnection.OnCallAPIURL.SetValid()
		status.PluginConnection.OnCallToken.SetValid()

		statusBody, err := io.ReadAll(res.Body)
		if err != nil {
			return fmt.Errorf("error reading response body: %v", err)
		}

		var engineStatus OnCallEngineStatus
		err = json.Unmarshal(statusBody, &engineStatus)
		if err != nil {
			return fmt.Errorf("error unmarshalling OnCallStatus: %v", err)
		}

		if engineStatus.ConnectionToGrafana.Connected {
			status.PluginConnection.GrafanaURLFromEngine.SetValid()
		} else {
			status.PluginConnection.GrafanaURLFromPlugin.SetInvalid(fmt.Sprintf("While contacting Grafana: %s from Engine: %s, received status: %d, additional: %s",
				engineStatus.ConnectionToGrafana.GrafanaURL,
				settings.OnCallAPIURL,
				engineStatus.ConnectionToGrafana.StatusCode,
				engineStatus.ConnectionToGrafana.Message))
		}

		status.APIURL = engineStatus.APIURL
		status.License = engineStatus.License
		status.CurrentlyUndergoingMaintenanceMessage = engineStatus.CurrentlyUndergoingMaintenanceMessage
		status.Version = engineStatus.Version
	}

	return nil
}

func (a *App) ValidateOnCallStatus(ctx context.Context, settings *OnCallPluginSettings) (*OnCallStatus, error) {
	status := OnCallStatus{
		PluginConnection: DefaultPluginConnection(),
	}

	if !status.PluginConnection.ValidateOnCallPluginSettings(settings) {
		return &status, nil
	}

	err := a.ValidateOnCallConnection(ctx, &status, settings)
	if err != nil {
		return &status, err
	}

	grafanaOK, err := a.ValidateGrafanaConnectionFromPlugin(&status, settings)
	if err != nil {
		return &status, err
	} else if !grafanaOK {
		return &status, nil
	}

	return &status, nil
}

func (a *App) HandleStatus(w http.ResponseWriter, req *http.Request) {
	if req.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	onCallPluginSettings, err := a.OnCallSettingsFromContext(req.Context())
	if err != nil {
		log.DefaultLogger.Error("Error getting settings from context", "error", err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	status, err := a.ValidateOnCallStatus(req.Context(), onCallPluginSettings)
	if err != nil {
		log.DefaultLogger.Error("Error validating oncall plugin settings", "error", err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Add("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(status); err != nil {
		http.Error(w, "Failed to encode response", http.StatusInternalServerError)
		return
	}
	w.WriteHeader(http.StatusOK)

	if status.AllOk() {
		a.doSync(req.Context(), false)
	}
}
