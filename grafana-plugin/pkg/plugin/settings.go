package plugin

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"regexp"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"github.com/grafana/grafana-plugin-sdk-go/backend"
	"github.com/grafana/grafana-plugin-sdk-go/backend/log"
	"github.com/grafana/grafana-plugin-sdk-go/backend/resource/httpadapter"
	grafana_plugin_build "github.com/grafana/grafana-plugin-sdk-go/build"
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
	OnCallAPIURL                  string `json:"oncall_api_url"`
	OnCallToken                   string `json:"oncall_token"`
	StackID                       int    `json:"stack_id"`
	OrgID                         int    `json:"org_id"`
	License                       string `json:"license"`
	GrafanaURL                    string `json:"grafana_url"`
	GrafanaToken                  string `json:"grafana_token"`
	RBACEnabled                   bool   `json:"rbac_enabled"`
	IncidentEnabled               bool   `json:"incident_enabled"`
	IncidentBackendURL            string `json:"incident_backend_url"`
	LabelsEnabled                 bool   `json:"labels_enabled"`
	ExternalServiceAccountEnabled bool   `json:"external_service_account_enabled"`
}

type OnCallSettingsCache struct {
	otherPluginSettingsLock   sync.Mutex
	otherPluginSettingsCache  map[string]map[string]interface{}
	otherPluginSettingsExpiry time.Time
}

const CLOUD_VERSION_PATTERN = `^(r\d+-v\d+\.\d+\.\d+|^github-actions-\d+)$`
const OSS_VERSION_PATTERN = `^(v\d+\.\d+\.\d+|dev-oss)$`
const CLOUD_LICENSE_NAME = "Cloud"
const OPEN_SOURCE_LICENSE_NAME = "OpenSource"
const INCIDENT_PLUGIN_ID = "grafana-incident-app"
const LABELS_PLUGIN_ID = "grafana-labels-app"
const OTHER_PLUGIN_EXPIRY_SECONDS = 60

func (a *App) OnCallSettingsFromContext(ctx context.Context) (*OnCallPluginSettings, error) {
	pluginContext := httpadapter.PluginConfigFromContext(ctx)
	var pluginSettingsJson OnCallPluginSettingsJSONData
	err := json.Unmarshal(pluginContext.AppInstanceSettings.JSONData, &pluginSettingsJson)
	if err != nil {
		err = fmt.Errorf("OnCallSettingsFromContext: json.Unmarshal: %w", err)
		log.DefaultLogger.Error(err.Error())
		return nil, err
	}

	settings := OnCallPluginSettings{
		StackID:      pluginSettingsJson.StackID,
		OrgID:        pluginSettingsJson.OrgID,
		OnCallAPIURL: pluginSettingsJson.OnCallAPIURL,
		License:      pluginSettingsJson.License,
		GrafanaURL:   pluginSettingsJson.GrafanaURL,
	}

	version := pluginContext.PluginVersion
	if version == "" {
		// older Grafana versions do not have the plugin version in the context
		buildInfo, err := grafana_plugin_build.GetBuildInfo()
		if err != nil {
			err = fmt.Errorf("OnCallSettingsFromContext: couldn't get plugin version: %w", err)
			log.DefaultLogger.Error(err.Error())
			return nil, err
		}
		version = buildInfo.Version
	}

	if settings.License == "" {
		cloudRe := regexp.MustCompile(CLOUD_VERSION_PATTERN)
		ossRe := regexp.MustCompile(OSS_VERSION_PATTERN)
		if ossRe.MatchString(version) {
			settings.License = OPEN_SOURCE_LICENSE_NAME
		} else if cloudRe.MatchString(version) {
			settings.License = CLOUD_LICENSE_NAME
		} else {
			return &settings, fmt.Errorf("jsonData.license is not set and version %s did not match a known pattern", version)
		}
	}

	settings.OnCallToken = strings.TrimSpace(pluginContext.AppInstanceSettings.DecryptedSecureJSONData["onCallApiToken"])
	cfg := backend.GrafanaConfigFromContext(ctx)
	if settings.GrafanaURL == "" {
		appUrl, err := cfg.AppURL()
		if err != nil {
			return &settings, fmt.Errorf("get GrafanaURL from provisioning failed (not set in jsonData), unable to fallback to grafana cfg")
		}
		settings.GrafanaURL = appUrl
		log.DefaultLogger.Info(fmt.Sprintf("Using Grafana URL from grafana cfg app url: %s", settings.GrafanaURL))
	} else {
		log.DefaultLogger.Info(fmt.Sprintf("Using Grafana URL from provisioning: %s", settings.GrafanaURL))
	}

	settings.RBACEnabled = cfg.FeatureToggles().IsEnabled("accessControlOnCall")
	if cfg.FeatureToggles().IsEnabled("externalServiceAccounts") {
		settings.GrafanaToken, err = cfg.PluginAppClientSecret()
		if err != nil {
			return &settings, err
		}
		settings.ExternalServiceAccountEnabled = true
	} else {
		settings.GrafanaToken = strings.TrimSpace(pluginContext.AppInstanceSettings.DecryptedSecureJSONData["grafanaToken"])
		settings.ExternalServiceAccountEnabled = false
	}

	otherPluginSettings := a.GetAllOtherPluginSettings(&settings)
	pluginSettings, exists := otherPluginSettings[INCIDENT_PLUGIN_ID]
	if exists {
		if value, ok := pluginSettings["enabled"].(bool); ok {
			settings.IncidentEnabled = value
		}
		if jsonData, ok := pluginSettings["jsonData"].(map[string]interface{}); ok {
			if value, ok := jsonData["backendUrl"].(string); ok {
				settings.IncidentBackendURL = value
			}
		}
	}
	pluginSettings, exists = otherPluginSettings[LABELS_PLUGIN_ID]
	if exists {
		if value, ok := pluginSettings["enabled"].(bool); ok {
			settings.LabelsEnabled = value
		}
	}
	return &settings, nil
}

func (a *App) GetAllOtherPluginSettings(settings *OnCallPluginSettings) map[string]map[string]interface{} {
	a.otherPluginSettingsLock.Lock()
	defer a.otherPluginSettingsLock.Unlock()

	if time.Now().Before(a.otherPluginSettingsExpiry) {
		return a.otherPluginSettingsCache
	}

	incidentPluginSettings, err := a.GetOtherPluginSettings(settings, INCIDENT_PLUGIN_ID)
	if err != nil {
		log.DefaultLogger.Error("getting incident plugin settings", "error", err)
	}
	labelsPluginSettings, err := a.GetOtherPluginSettings(settings, LABELS_PLUGIN_ID)
	if err != nil {
		log.DefaultLogger.Error("getting incident plugin settings", "error", err)
	}

	otherPluginSettings := make(map[string]map[string]interface{})
	otherPluginSettings[INCIDENT_PLUGIN_ID] = incidentPluginSettings
	otherPluginSettings[LABELS_PLUGIN_ID] = labelsPluginSettings

	a.otherPluginSettingsCache = otherPluginSettings
	a.otherPluginSettingsExpiry = time.Now().Add(OTHER_PLUGIN_EXPIRY_SECONDS * time.Second)
	return a.otherPluginSettingsCache
}

func (a *App) GetOtherPluginSettings(settings *OnCallPluginSettings, pluginID string) (map[string]interface{}, error) {
	atomic.AddInt32(&a.SettingsCallCount, 1)
	reqURL, err := url.JoinPath(settings.GrafanaURL, fmt.Sprintf("api/plugins/%s/settings", pluginID))
	if err != nil {
		return nil, fmt.Errorf("error creating URL: %v", err)
	}

	req, err := http.NewRequest("GET", reqURL, nil)
	if err != nil {
		return nil, fmt.Errorf("error creating creating new request: %v", err)
	}
	req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", settings.GrafanaToken))

	res, err := a.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("error making request: %v, %v", err, reqURL)
	}
	defer res.Body.Close()

	if res.StatusCode != 200 {
		return nil, nil
	}

	body, err := io.ReadAll(res.Body)
	if err != nil {
		return nil, fmt.Errorf("error reading response: %v", err)
	}

	var result map[string]interface{}
	err = json.Unmarshal(body, &result)
	if err != nil {
		return nil, fmt.Errorf("failed to parse JSON response: %v", err)
	}

	return result, fmt.Errorf("no jsonData for plugin %s", pluginID)
}

func (a *App) SaveOnCallSettings(settings *OnCallPluginSettings) error {
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

func (a *App) GetSyncData(ctx context.Context, settings *OnCallPluginSettings) (*OnCallSync, error) {
	startGetSyncData := time.Now()
	defer func() {
		elapsed := time.Since(startGetSyncData)
		log.DefaultLogger.Info("GetSyncData", "time", elapsed)
	}()

	onCallPluginSettings, err := a.OnCallSettingsFromContext(ctx)
	if err != nil {
		return nil, fmt.Errorf("error getting settings from context = %v", err)
	}

	onCallSync := OnCallSync{
		Settings: *settings,
	}
	onCallSync.Users, err = a.GetAllUsersWithPermissions(onCallPluginSettings)
	if err != nil {
		return nil, fmt.Errorf("error getting users = %v", err)
	}

	onCallSync.Teams, err = a.GetAllTeams(onCallPluginSettings)
	if err != nil {
		return nil, fmt.Errorf("error getting teams = %v", err)
	}

	teamMembers, err := a.GetAllTeamMembers(onCallPluginSettings, onCallSync.Teams)
	if err != nil {
		return nil, fmt.Errorf("error getting team members = %v", err)
	}
	onCallSync.TeamMembers = teamMembers

	return &onCallSync, nil
}
