package plugin

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"

	"github.com/grafana/grafana-plugin-sdk-go/backend"
	"github.com/grafana/grafana-plugin-sdk-go/backend/log"
)

type LookupUser struct {
	ID        int    `json:"id"`
	Name      string `json:"name"`
	Login     string `json:"login"`
	Email     string `json:"email"`
	AvatarURL string `json:"avatarUrl"`
}

type OrgUser struct {
	ID        int    `json:"userId"`
	Name      string `json:"name"`
	Login     string `json:"login"`
	Email     string `json:"email"`
	AvatarURL string `json:"avatarUrl"`
	Role      string `json:"role"`
}

type OnCallUser struct {
	ID          int                `json:"id"`
	Name        string             `json:"name"`
	Login       string             `json:"login"`
	Email       string             `json:"email"`
	Role        string             `json:"role"`
	AvatarURL   string             `json:"avatar_url"`
	Permissions []OnCallPermission `json:"permissions"`
	Teams       []int              `json:"teams"`
}

func (a *App) GetUser(settings *OnCallPluginSettings, user *backend.User) (*OnCallUser, error) {
	users, err := a.GetAllUsers(settings)
	if err != nil {
		return nil, err
	}

	for _, u := range users {
		if u.Login == user.Login {
			return &u, nil
		}
	}
	return nil, fmt.Errorf("user %s not found", user.Login)
}

func (a *App) GetUserForHeader(settings *OnCallPluginSettings, user *backend.User) (*OnCallUser, error) {
	onCallUser, err := a.GetUser(settings, user)
	if err != nil {
		return nil, err
	}

	if settings.ExternalServiceAccountEnabled {
		onCallUser.Teams, err = a.GetTeamsForUser(settings, onCallUser)
		if err != nil {
			return nil, err
		}
	}
	if settings.RBACEnabled {
		onCallUser.Permissions, err = a.GetPermissions(settings, onCallUser)
		if err != nil {
			return nil, err
		}
	}
	return onCallUser, nil
}

func (a *App) GetAllUsers(settings *OnCallPluginSettings) ([]OnCallUser, error) {
	reqURL, err := url.Parse(settings.GrafanaURL)
	if err != nil {
		return nil, fmt.Errorf("error parsing URL: %+v", err)
	}

	reqURL.Path += "api/org/users"

	req, err := http.NewRequest("GET", reqURL.String(), nil)
	if err != nil {
		return nil, fmt.Errorf("error creating new request: %+v", err)
	}
	req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", settings.GrafanaToken))

	res, err := a.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("error making request: %+v", err)
	}
	defer res.Body.Close()

	body, err := io.ReadAll(res.Body)
	if err != nil {
		return nil, fmt.Errorf("error reading response: %+v", err)
	}

	var result []OrgUser
	err = json.Unmarshal(body, &result)
	if err != nil {
		return nil, fmt.Errorf("failed to parse JSON response: %v", err)
	}

	if res.StatusCode == 200 {
		var users []OnCallUser
		for _, orgUser := range result {
			onCallUser := OnCallUser{
				ID:        orgUser.ID,
				Name:      orgUser.Name,
				Login:     orgUser.Login,
				Email:     orgUser.Email,
				AvatarURL: orgUser.AvatarURL,
				Role:      orgUser.Role,
			}
			users = append(users, onCallUser)
		}
		return users, nil
	}
	return nil, fmt.Errorf("http status %s", res.Status)
}

func (a *App) GetAllUsersWithPermissions(settings *OnCallPluginSettings) ([]OnCallUser, error) {
	onCallUsers, err := a.GetAllUsers(settings)
	if err != nil {
		return nil, err
	}
	if settings.RBACEnabled {
		permissions, err := a.GetAllPermissions(settings)
		if err != nil {
			return nil, err
		}
		for i := range onCallUsers {
			actions, exists := permissions["1"]
			if exists {
				onCallUsers[i].Permissions = []OnCallPermission{}
				for action, _ := range actions {
					onCallUsers[i].Permissions = append(onCallUsers[i].Permissions, OnCallPermission{Action: action})
				}
			} else {
				log.DefaultLogger.Error(fmt.Sprintf("Did not find permissions for user %s", onCallUsers[i].Login))
			}
		}
	}
	return onCallUsers, nil
}
