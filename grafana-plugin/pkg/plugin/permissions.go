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

type RBACPermission struct {
	Action string `json:"action"`
}

// https://grafana.com/docs/grafana/latest/developers/http_api/access_control/#list-permissions-assigned-to-a-user
func (a *App) GetPermissionsForUser(settings *OnCallPluginSettings, onCallUser *OnCallUser) ([]RBACPermission, error) {
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

	var permissions []RBACPermission
	err = json.Unmarshal(body, &permissions)
	if err != nil {
		return nil, fmt.Errorf("failed to parse JSON response: %v body=%v", err, string(body))
	}

	if res.StatusCode == 200 {
		var filtered []RBACPermission
		for _, permission := range permissions {
			for _, pluginId := range a.pluginIDsToSyncPermissions {
				if strings.HasPrefix(permission.Action, pluginId) {
					filtered = append(filtered, permission)
					break
				}
			}
		}
		return filtered, nil
	}
	return nil, fmt.Errorf("no permissions for %s, http status %s", onCallUser.Login, res.Status)
}

func (a *App) getPermissionsForPlugin(settings *OnCallPluginSettings, pluginId string) (map[string]map[string]interface{}, error) {
	reqURL, err := url.Parse(settings.GrafanaURL)
	if err != nil {
		return nil, fmt.Errorf("error parsing URL: %v", err)
	}

	reqURL.Path += "api/access-control/users/permissions/search"
	q := reqURL.Query()
	q.Set("actionPrefix", pluginId)
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

func mergePermissions(permissions1, permissions2 map[string]map[string]interface{}) map[string]map[string]interface{} {
	if permissions1 == nil {
		return permissions2
	}

	if permissions2 == nil {
		return permissions1
	}

	for key, value := range permissions2 {
		if _, ok := permissions1[key]; !ok {
			permissions1[key] = value
		} else {
			for k, v := range value {
				permissions1[key][k] = v
			}
		}
	}

	return permissions1
}

func (a *App) GetAllPermissions(settings *OnCallPluginSettings) (map[string]map[string]interface{}, error) {
	atomic.AddInt32(&a.AllPermissionsCallCount, 1)

	var permissions map[string]map[string]interface{}

	for _, pluginId := range a.pluginIDsToSyncPermissions {
		pluginPermissions, err := a.getPermissionsForPlugin(settings, pluginId)
		if err != nil {
			return nil, fmt.Errorf("error getting permissions for plugin %s: %v", pluginId, err)
		}
		permissions = mergePermissions(permissions, pluginPermissions)
	}

	return permissions, nil
}
