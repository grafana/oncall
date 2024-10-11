package plugin

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"sync/atomic"
)

type Teams struct {
	Teams []Team `json:"teams"`
}

type Team struct {
	ID        int    `json:"id"`
	Name      string `json:"name"`
	Email     string `json:"email"`
	AvatarURL string `json:"avatarUrl"`
}

type OnCallTeam struct {
	ID        int    `json:"team_id"`
	Name      string `json:"name"`
	Email     string `json:"email"`
	AvatarURL string `json:"avatar_url"`
}

func (a *OnCallTeam) Equal(b *OnCallTeam) bool {
	if a.ID != b.ID {
		return false
	}
	if a.Name != b.Name {
		return false
	}
	if a.Email != b.Email {
		return false
	}
	if a.AvatarURL != b.AvatarURL {
		return false
	}
	return true
}

func (a *App) GetTeamsForUser(settings *OnCallPluginSettings, onCallUser *OnCallUser) ([]int, error) {
	atomic.AddInt32(&a.TeamForUserCallCount, 1)
	reqURL, err := url.JoinPath(settings.GrafanaURL, fmt.Sprintf("api/users/%d/teams", onCallUser.ID))
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

	var result []Team
	err = json.Unmarshal(body, &result)
	if err != nil {
		return nil, fmt.Errorf("failed to parse JSON response: %v body=%v", err, string(body))
	}

	if res.StatusCode == 200 {
		var teams []int
		for _, team := range result {
			teams = append(teams, team.ID)
		}
		return teams, nil
	}
	return nil, fmt.Errorf("no teams for %s, http status %s", onCallUser.Login, res.Status)
}

func (a *App) GetAllTeams(settings *OnCallPluginSettings) ([]OnCallTeam, error) {
	atomic.AddInt32(&a.AllTeamsCallCount, 1)
	reqURL, err := url.Parse(settings.GrafanaURL)
	if err != nil {
		return nil, fmt.Errorf("error parsing URL: %v", err)
	}

	reqURL.Path += "api/teams/search"
	q := reqURL.Query()
	q.Set("perpage", "100000")
	reqURL.RawQuery = q.Encode()

	req, err := http.NewRequest("GET", reqURL.String(), nil)
	if err != nil {
		return nil, fmt.Errorf("error creating new request: %v", err)
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

	var result Teams
	err = json.Unmarshal(body, &result)
	if err != nil {
		return nil, fmt.Errorf("failed to parse JSON response: %v body=%v", err, string(body))
	}

	if res.StatusCode == 200 {
		var teams []OnCallTeam
		for _, team := range result.Teams {
			onCallTeam := OnCallTeam{
				ID:        team.ID,
				Name:      team.Name,
				Email:     team.Email,
				AvatarURL: team.AvatarURL,
			}
			teams = append(teams, onCallTeam)
		}
		return teams, nil
	}
	return nil, fmt.Errorf("http status %s", res.Status)
}

func (a *App) GetTeamsMembersForTeam(settings *OnCallPluginSettings, onCallTeam *OnCallTeam) ([]int, error) {
	atomic.AddInt32(&a.TeamMembersForTeamCallCount, 1)
	reqURL, err := url.JoinPath(settings.GrafanaURL, fmt.Sprintf("api/teams/%d/members", onCallTeam.ID))
	if err != nil {
		return nil, fmt.Errorf("error creating URL: %+v", err)
	}

	req, err := http.NewRequest("GET", reqURL, nil)
	if err != nil {
		return nil, fmt.Errorf("error creating creating new request: %+v", err)
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
		return nil, fmt.Errorf("failed to parse JSON response: %v body=%v", err, string(body))
	}

	if res.StatusCode == 200 {
		var members []int
		for _, user := range result {
			members = append(members, user.ID)
		}
		return members, nil
	}
	return nil, fmt.Errorf("http status %s", res.Status)
}

func (a *App) GetAllTeamMembers(settings *OnCallPluginSettings, onCallTeams []OnCallTeam) (map[int][]int, error) {
	teamMapping := map[int][]int{}
	for _, team := range onCallTeams {
		teamMembers, err := a.GetTeamsMembersForTeam(settings, &team)
		if err != nil {
			return nil, err
		}
		teamMapping[team.ID] = teamMembers
	}
	return teamMapping, nil
}
