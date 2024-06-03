package plugin

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"

	"github.com/grafana/grafana-plugin-sdk-go/backend"
	"github.com/grafana/grafana-plugin-sdk-go/backend/log"
)

func (a *App) GetUserID(user *backend.User, settings OnCallPluginSettings) (int, error) {
	reqURL, err := url.Parse(settings.GrafanaURL)
	if err != nil {
		return 0, err
	}

	reqURL.Path += "api/users/lookup"
	q := reqURL.Query()
	q.Set("loginOrEmail", user.Login)
	reqURL.RawQuery = q.Encode()

	req, err := http.NewRequest("GET", reqURL.String(), nil)
	if err != nil {
		return 0, err
	}

	req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", settings.GrafanaToken))

	res, err := a.httpClient.Do(req)
	if err != nil {
		return 0, err
	}
	defer res.Body.Close()

	body, err := io.ReadAll(res.Body)
	if err != nil {
		return 0, err
	}

	log.DefaultLogger.Info(fmt.Sprintf("User Response %s %s %s", reqURL.String(), res.Status, body))

	var result map[string]interface{}
	err = json.Unmarshal(body, &result)
	if err != nil {
		err = fmt.Errorf("Error unmarshalling JSON: %+v", err)
		log.DefaultLogger.Error(err.Error())
		return 0, err
	}

	if res.StatusCode == 200 {
		id, ok := result["id"].(float64)
		if !ok {
			err = fmt.Errorf("Error no id field in object: %+v", err)
			return 0, err
		}
		return int(id), nil
	}

	return 0, fmt.Errorf("User %s not found", user.Login)
}

func (a *App) SetPermissionsHeader(userID int, settings OnCallPluginSettings, req *http.Request) error {
	permissionsURL, err := url.JoinPath(settings.GrafanaURL, fmt.Sprintf("api/access-control/users/%d/permissions", userID))
	if err != nil {
		return err
	}

	permissionsReq, err := http.NewRequest("GET", permissionsURL, nil)
	if err != nil {
		return err
	}

	permissionsReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", settings.GrafanaToken))

	res, err := a.httpClient.Do(permissionsReq)
	if err != nil {
		return err
	}
	defer res.Body.Close()

	body, err := io.ReadAll(res.Body)
	if err != nil {
		return err
	}

	log.DefaultLogger.Info(fmt.Sprintf("Permissions %s %s %s", permissionsURL, res.Status, body))
	if len(body) > 0 && res.StatusCode == 200 {
		req.Header.Set("X-Grafana-User-Permissions", string(body))
	}
	return nil
}

func (a *App) SetTeamsHeader(userID int, settings OnCallPluginSettings, req *http.Request) error {
	teamsURL, err := url.JoinPath(settings.GrafanaURL, fmt.Sprintf("api/users/%d/teams", userID))
	if err != nil {
		return err
	}

	teamsReq, err := http.NewRequest("GET", teamsURL, nil)
	if err != nil {
		return err
	}

	teamsReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", settings.GrafanaToken))

	res, err := a.httpClient.Do(teamsReq)
	if err != nil {
		return err
	}
	defer res.Body.Close()

	body, err := io.ReadAll(res.Body)
	if err != nil {
		return err
	}

	log.DefaultLogger.Info(fmt.Sprintf("Teams %s %s %s", teamsURL, res.Status, body))
	if len(body) > 0 && res.StatusCode == 200 {
		req.Header.Set("X-Grafana-User-Teams", string(body))
	}
	return nil
}

func (a *App) SaveOnCallSettings(settings OnCallPluginSettings) error {
	data := OnCallPluginJSONData{
		JSONData: OnCallPluginSettingsJSONData{
			OnCallAPIURL:     settings.OnCallAPIURL,
			StackID:          settings.StackID,
			OrgID:            settings.OrgID,
			License:          settings.License,
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
