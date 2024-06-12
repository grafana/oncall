package plugin

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"

	"github.com/grafana/grafana-plugin-sdk-go/backend"
	"github.com/grafana/grafana-plugin-sdk-go/backend/log"
	"github.com/grafana/grafana-plugin-sdk-go/backend/resource/httpadapter"
)

type OnCallPluginSettingsJSONData struct {
	OnCallAPIURL string `json:"onCallApiUrl"`
	StackID      int    `json:"stackId,omitempty"`
	OrgID        int    `json:"orgId,omitempty"`
	License      string `json:"license"`
	GrafanaURL   string `json:"grafanaUrl"`
}

type OnCallPluginSettingsSecureJSONData struct {
	OnCallToken  string `json:"onCallApiToken"`
	GrafanaToken string `json:"grafanaToken,omitempty"`
}

type OnCallPluginJSONData struct {
	JSONData       OnCallPluginSettingsJSONData       `json:"jsonData"`
	SecureJSONData OnCallPluginSettingsSecureJSONData `json:"secureJsonData"`
	Enabled        bool                               `json:"enabled"`
	Pinned         bool                               `json:"pinned"`
}

type OnCallPluginSettings struct {
	OnCallAPIURL       string
	StackID            int
	OrgID              int
	GrafanaToken       string
	OnCallToken        string
	GrafanaURL         string
	License            string
	RBACEnabled        bool
	IncidentEnabled    bool
	IncidentBackendURL string
	LabelsEnabled      bool
}

func (a *App) OnCallSettingsFromContext(ctx context.Context) (OnCallPluginSettings, error) {
	pluginContext := httpadapter.PluginConfigFromContext(ctx)
	var settings OnCallPluginSettings
	err := json.Unmarshal(pluginContext.AppInstanceSettings.JSONData, &settings)
	if err != nil {
		err = fmt.Errorf("OnCallSettingsFromContext: json.Unmarshal: %w", err)
		log.DefaultLogger.Error(err.Error())
		return settings, err
	}

	settings.OnCallToken = strings.TrimSpace(pluginContext.AppInstanceSettings.DecryptedSecureJSONData["onCallApiToken"])
	cfg := backend.GrafanaConfigFromContext(ctx)
	grafanaURL, err := cfg.AppURL()
	if err != nil {
		// Fallback to GrafanaURL already being set in settings outside backend plugin from provisioning or UI
		if settings.GrafanaURL == "" {
			return settings, fmt.Errorf("Fallback GrafanaURL failed (not set in jsonData): %+v", settings)
		}
	} else {
		settings.GrafanaURL = grafanaURL
	}

	settings.RBACEnabled = cfg.FeatureToggles().IsEnabled("accessControlOnCall")
	if cfg.FeatureToggles().IsEnabled("externalServiceAccounts") {
		settings.GrafanaToken, err = cfg.PluginAppClientSecret()
		if err != nil {
			return settings, err
		}
	} else {
		settings.GrafanaToken = strings.TrimSpace(pluginContext.AppInstanceSettings.DecryptedSecureJSONData["grafanaToken"])
	}

	var jsonData map[string]interface{}
	settings.IncidentEnabled, jsonData, err = a.GetOtherPluginSettings(&settings, "grafana-incident-app")
	if err != nil {
		return settings, err
	}
	if jsonData != nil {
		if value, ok := jsonData["backendUrl"].(string); ok {
			settings.IncidentBackendURL = value
		}
	}
	settings.LabelsEnabled, _, err = a.GetOtherPluginSettings(&settings, "grafana-labels-app")
	if err != nil {
		return settings, err
	}

	return settings, nil
}

func (a *App) SaveOnCallSettings(settings OnCallPluginSettings) error {
	data := OnCallPluginJSONData{
		JSONData: OnCallPluginSettingsJSONData{
			OnCallAPIURL: settings.OnCallAPIURL,
			StackID:      settings.StackID,
			OrgID:        settings.OrgID,
			License:      settings.License,
			GrafanaURL:   settings.GrafanaURL,
		},
		SecureJSONData: OnCallPluginSettingsSecureJSONData{
			OnCallToken:  settings.OnCallToken,
			GrafanaToken: settings.GrafanaToken,
		},
		Enabled: true,
		Pinned:  true,
	}
	body, err := json.Marshal(data)
	if err != nil {
		return fmt.Errorf("Marshal OnCall settings JSON: %w", err)
	}

	settingsUrl, err := url.JoinPath(settings.GrafanaURL, fmt.Sprintf("api/plugins/grafana-oncall-app/settings"))
	if err != nil {
		return err
	}

	settingsReq, err := http.NewRequest("POST", settingsUrl, bytes.NewReader(body))
	if err != nil {
		return err
	}

	settingsReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", settings.GrafanaToken))
	settingsReq.Header.Set("Content-Type", "application/json")

	res, err := a.httpClient.Do(settingsReq)
	if err != nil {
		return err
	}
	defer res.Body.Close()

	return nil
}

func (a *App) GetOtherPluginSettings(settings *OnCallPluginSettings, pluginID string) (bool, map[string]interface{}, error) {
	reqURL, err := url.JoinPath(settings.GrafanaURL, fmt.Sprintf("api/plugins/%s/settings", pluginID))
	if err != nil {
		return false, nil, fmt.Errorf("error creating URL: %+v", err)
	}

	req, err := http.NewRequest("GET", reqURL, nil)
	if err != nil {
		return false, nil, fmt.Errorf("error creating creating new request: %+v", err)
	}
	req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", settings.GrafanaToken))

	res, err := a.httpClient.Do(req)
	if err != nil {
		return false, nil, fmt.Errorf("error making request: %+v", err)
	}
	defer res.Body.Close()

	if res.StatusCode != 200 {
		return false, nil, nil
	}

	body, err := io.ReadAll(res.Body)
	if err != nil {
		return false, nil, fmt.Errorf("error reading response: %+v", err)
	}

	var result map[string]interface{}
	err = json.Unmarshal(body, &result)
	if err != nil {
		return false, nil, fmt.Errorf("failed to parse JSON response: %v", err)
	}

	var enabled = false
	if value, ok := result["enabled"].(bool); ok {
		enabled = value
	}
	if jsonData, ok := result["jsonData"].(map[string]interface{}); ok {
		return enabled, jsonData, nil
	}
	return enabled, nil, fmt.Errorf("no jsonData for plugin %s", pluginID)
}

func (a *App) GetSyncData(ctx context.Context, settings *OnCallPluginSettings) (*OnCallSync, error) {
	onCallPluginSettings, err := a.OnCallSettingsFromContext(ctx)
	if err != nil {
		return nil, fmt.Errorf("error getting settings from context = %+v", err)
	}

	onCallSync := OnCallSync{
		Config: OnCallFeaturesConfig{
			RBACEnabled:        settings.RBACEnabled,
			IncidentEnabled:    settings.IncidentEnabled,
			IncidentBackendURL: settings.IncidentBackendURL,
			LabelsEnabled:      settings.LabelsEnabled,
		},
	}
	onCallSync.Users, err = a.GetAllUsersWithPermissions(&onCallPluginSettings)
	if err != nil {
		return nil, fmt.Errorf("error getting users = %+v", err)
	}

	onCallSync.Teams, err = a.GetAllTeams(&onCallPluginSettings)
	if err != nil {
		return nil, fmt.Errorf("error getting teams = %+v", err)
	}

	teamMembers, err := a.GetAllTeamMembers(&onCallPluginSettings, onCallSync.Teams)
	if err != nil {
		return nil, fmt.Errorf("error getting team members = %+v", err)
	}
	onCallSync.TeamMembers = teamMembers

	return &onCallSync, nil
}
