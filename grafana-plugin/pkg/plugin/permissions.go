package plugin

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"sync/atomic"
)

type OnCallPermission struct {
	Action string `json:"action"`
}

func (a *App) GetPermissions(settings *OnCallPluginSettings, onCallUser *OnCallUser) ([]OnCallPermission, error) {
	atomic.AddInt32(&a.PermissionsCallCount, 1)
	reqURL, err := url.JoinPath(settings.GrafanaURL, fmt.Sprintf("api/access-control/users/%d/permissions", onCallUser.ID))
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
		return nil, fmt.Errorf("error making request: %v", err)
	}
	defer res.Body.Close()

	body, err := io.ReadAll(res.Body)
	if err != nil {
		return nil, fmt.Errorf("error reading response: %v", err)
	}

	var permissions []OnCallPermission
	err = json.Unmarshal(body, &permissions)
	if err != nil {
		return nil, fmt.Errorf("failed to parse JSON response: %v body=%v", err, string(body))
	}

	if res.StatusCode == 200 {
		var filtered []OnCallPermission
		for _, permission := range permissions {
			if strings.HasPrefix(permission.Action, settings.PluginID) {
				filtered = append(filtered, permission)
			}
		}
		return filtered, nil
	}
	return nil, fmt.Errorf("no permissions for %s, http status %s", onCallUser.Login, res.Status)
}

func (a *App) GetAllPermissions(settings *OnCallPluginSettings) (map[string]map[string]interface{}, error) {
	atomic.AddInt32(&a.AllPermissionsCallCount, 1)
	reqURL, err := url.Parse(settings.GrafanaURL)
	if err != nil {
		return nil, fmt.Errorf("error parsing URL: %v", err)
	}

	reqURL.Path += "api/access-control/users/permissions/search"
	q := reqURL.Query()
	q.Set("actionPrefix", settings.PluginID)
	reqURL.RawQuery = q.Encode()

	req, err := http.NewRequest("GET", reqURL.String(), nil)
	if err != nil {
		return nil, fmt.Errorf("error creating creating new request: %v", err)
	}
	req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", settings.GrafanaToken))

	res, err := a.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("error making request: %v", err)
	}
	defer res.Body.Close()

	body, err := io.ReadAll(res.Body)
	if err != nil {
		return nil, fmt.Errorf("error reading response: %v", err)
	}

	var permissions map[string]map[string]interface{}
	err = json.Unmarshal(body, &permissions)
	if err != nil {
		return nil, fmt.Errorf("failed to parse JSON response: %v body=%v", err, string(body))
	}

	if res.StatusCode == 200 {
		return permissions, nil
	}
	return nil, fmt.Errorf("no permissions available, http status %s", res.Status)
}
