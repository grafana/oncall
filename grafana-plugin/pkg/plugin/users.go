package plugin

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"sort"
	"strconv"
	"sync"
	"sync/atomic"
	"time"

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

func (a *OnCallUser) Equal(b *OnCallUser) bool {
	if a.ID != b.ID {
		return false
	}
	if a.Name != b.Name {
		return false
	}
	if a.Login != b.Login {
		return false
	}
	if a.Email != b.Email {
		return false
	}
	if a.Role != b.Role {
		return false
	}
	if a.AvatarURL != b.AvatarURL {
		return false
	}

	if len(a.Permissions) != len(b.Permissions) {
		return false
	}
	sort.Slice(a.Permissions, func(i, j int) bool {
		return a.Permissions[i].Action < a.Permissions[j].Action
	})
	sort.Slice(b.Permissions, func(i, j int) bool {
		return b.Permissions[i].Action < b.Permissions[j].Action
	})
	for i := range a.Permissions {
		if a.Permissions[i].Action != b.Permissions[i].Action {
			return false
		}
	}

	if len(a.Teams) != len(b.Teams) {
		return false
	}
	sort.Slice(a.Teams, func(i, j int) bool {
		return a.Teams[i] < a.Teams[j]
	})
	sort.Slice(b.Teams, func(i, j int) bool {
		return b.Teams[i] < b.Teams[j]
	})
	for i := range a.Teams {
		if a.Teams[i] != b.Teams[i] {
			return false
		}
	}
	return true
}

type OnCallUserCache struct {
	allUsersLock   sync.Mutex
	allUsersCache  map[string]*OnCallUser
	allUsersExpiry time.Time

	lockInitLock sync.Mutex
	userLocks    map[string]*sync.Mutex
	userCache    map[string]*OnCallUser
	userExpiry   map[string]time.Time
}

const USER_EXPIRY_SECONDS = 60

func NewOnCallUserCache() *OnCallUserCache {
	return &OnCallUserCache{
		allUsersCache: make(map[string]*OnCallUser),
		userLocks:     make(map[string]*sync.Mutex),
		userCache:     make(map[string]*OnCallUser),
		userExpiry:    make(map[string]time.Time),
	}
}

func (c *OnCallUserCache) GetUserLock(user string) *sync.Mutex {
	c.lockInitLock.Lock()
	defer c.lockInitLock.Unlock()
	lock, exists := c.userLocks[user]
	if !exists {
		lock = &sync.Mutex{}
		c.userLocks[user] = lock
	}
	return lock
}

func (a *App) GetUser(settings *OnCallPluginSettings, user *backend.User) (*OnCallUser, error) {
	log.DefaultLogger.Info("GetUser", "user", user)
	a.allUsersLock.Lock()
	defer a.allUsersLock.Unlock()

	if time.Now().Before(a.allUsersExpiry) {
		ocu, exists := a.allUsersCache[user.Login]
		if !exists {
			return nil, fmt.Errorf("user %s not found", user.Login)
		}
		return ocu, nil
	}

	users, err := a.GetAllUsers(settings)
	if err != nil {
		return nil, err
	}

	var oncallUser *OnCallUser
	allUsersCache := make(map[string]*OnCallUser)
	for i := range users {
		u := &users[i]
		allUsersCache[u.Login] = u
		if u.Login == user.Login {
			oncallUser = u
		}
	}

	a.allUsersCache = allUsersCache
	a.allUsersExpiry = time.Now().Add(USER_EXPIRY_SECONDS * time.Second)

	if oncallUser == nil {
		return nil, fmt.Errorf("user %s not found", user.Login)
	}
	return oncallUser, nil
}

func (a *App) GetUserForHeader(settings *OnCallPluginSettings, user *backend.User) (*OnCallUser, error) {
	userLock := a.GetUserLock(user.Login)
	userLock.Lock()
	defer userLock.Unlock()

	ue, expiryExists := a.userExpiry[user.Login]
	if expiryExists && time.Now().Before(ue) {
		ocu, userExists := a.userCache[user.Login]
		if !userExists {
			return nil, fmt.Errorf("user %s not found", user.Login)
		}
		return ocu, nil
	}

	onCallUser, err := a.GetUser(settings, user)
	if err != nil {
		return nil, err
	}

	// manually created service account with Admin role doesn't have permission to get user teams
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

	a.userCache[user.Login] = onCallUser
	a.userExpiry[user.Login] = time.Now().Add(USER_EXPIRY_SECONDS * time.Second)
	return onCallUser, nil
}

func (a *App) GetAllUsers(settings *OnCallPluginSettings) ([]OnCallUser, error) {
	atomic.AddInt32(&a.AllUsersCallCount, 1)
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
		return nil, fmt.Errorf("failed to parse JSON response: %v body=%v", err, string(body))
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
			userId := strconv.Itoa(onCallUsers[i].ID)
			actions, exists := permissions[userId]
			if exists {
				onCallUsers[i].Permissions = []OnCallPermission{}
				for action, _ := range actions {
					onCallUsers[i].Permissions = append(onCallUsers[i].Permissions, OnCallPermission{Action: action})
				}
			} else {
				log.DefaultLogger.Error("Did not find permissions for user", "user", onCallUsers[i].Login, "id", userId)
			}
		}
	}
	return onCallUsers, nil
}
