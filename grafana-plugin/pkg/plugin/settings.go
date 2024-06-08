package plugin

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
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
	OnCallAPIURL string
	StackID      int
	OrgID        int
	GrafanaToken string
	OnCallToken  string
	GrafanaURL   string
	License      string
	RBACEnabled  bool
}

func OnCallSettingsFromContext(ctx context.Context) (OnCallPluginSettings, error) {
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
	settings.GrafanaURL, err = cfg.AppURL()
	if err != nil {
		return settings, err
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

	return settings, nil
}

func (a *App) SaveOnCallSettings(settings OnCallPluginSettings) error {
	data := OnCallPluginJSONData{
		JSONData: OnCallPluginSettingsJSONData{
			OnCallAPIURL: settings.OnCallAPIURL,
			StackID:      settings.StackID,
			OrgID:        settings.OrgID,
			License:      settings.License,
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
