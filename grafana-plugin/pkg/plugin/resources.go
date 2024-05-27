package plugin

import (
	"bytes"
	"encoding/json"
	"fmt"
	"github.com/grafana/grafana-plugin-sdk-go/backend"
	"github.com/grafana/grafana-plugin-sdk-go/backend/log"
	"github.com/grafana/grafana-plugin-sdk-go/backend/resource/httpadapter"
	"io"
	"net/http"
	"net/url"
	"strconv"
)

type XInstanceContextJSONData struct {
	StackId      string `json:"stack_id,omitempty"`
	OrgId        string `json:"org_id,omitempty"`
	GrafanaToken string `json:"grafana_token"`
}

type XGrafanaContextJSONData struct {
	ID          int    `json:"UserID"`
	IsAnonymous bool   `json:"IsAnonymous"`
	Name        string `json:"Name"`
	Login       string `json:"Login"`
	Email       string `json:"Email"`
	Role        string `json:"Role"`
}

type UserIDJSONData struct {
	ID int `json:"intField"`
}

func SetXInstanceContextHeader(settings OnCallPluginSettings, req *http.Request) error {
	xInstanceContext := XInstanceContextJSONData{
		StackId:      strconv.Itoa(settings.StackID),
		OrgId:        strconv.Itoa(settings.OrgID),
		GrafanaToken: settings.GrafanaToken,
	}
	xInstanceContextHeader, err := json.Marshal(xInstanceContext)
	if err != nil {
		return err
	}
	req.Header.Set("X-Instance-Context", string(xInstanceContextHeader))
	return nil
}

func SetXGrafanaContextHeader(user *backend.User, userID int, req *http.Request) error {
	var xGrafanaContext XGrafanaContextJSONData
	if user == nil {
		xGrafanaContext = XGrafanaContextJSONData{
			IsAnonymous: true,
		}
	} else {
		xGrafanaContext = XGrafanaContextJSONData{
			ID:          userID,
			IsAnonymous: false,
			Name:        user.Name,
			Login:       user.Login,
			Email:       user.Email,
			Role:        user.Role,
		}
	}
	xGrafanaContextHeader, err := json.Marshal(xGrafanaContext)
	if err != nil {
		return err
	}
	req.Header.Set("X-Grafana-Context", string(xGrafanaContextHeader))
	return nil
}

func SetAuthorizationHeader(settings OnCallPluginSettings, req *http.Request) {
	req.Header.Set("Authorization", settings.OnCallToken)
}

func (a *App) GetUserID(user *backend.User, settings OnCallPluginSettings) (int, error) {
	reqURL, err := url.Parse(settings.GrafanaURL)
	if err != nil {
		return 0, err
	}

	reqURL.Path += "api/users"
	q := reqURL.Query()
	q.Set("login", user.Login)
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

	var result []map[string]interface{}
	err = json.Unmarshal(body, &result)
	if err != nil {
		err = fmt.Errorf("Error unmarshalling JSON: %+v", err)
		log.DefaultLogger.Error(err.Error())
		return 0, err
	}

	if len(result) > 0 && res.StatusCode == 200 {
		id, ok := result[0]["id"].(float64)
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
	permissionsURL, err := url.JoinPath(settings.GrafanaURL, fmt.Sprintf("api/users/%d/teams", userID))
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

	log.DefaultLogger.Info(fmt.Sprintf("Teams %s %s %s", permissionsURL, res.Status, body))
	if len(body) > 0 && res.StatusCode == 200 {
		req.Header.Set("X-Grafana-User-Teams", string(body))
	}
	return nil
}

func (a *App) handleOnCall(w http.ResponseWriter, req *http.Request) {
	proxyMethod := req.Method
	var proxyBody string
	bodyReader := bytes.NewReader([]byte(proxyBody))

	onCallPluginSettings, err := OnCallSettingsFromContext(req.Context())
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	log.DefaultLogger.Info(fmt.Sprintf("OnCallSettings %+v", onCallPluginSettings))

	user := httpadapter.UserFromContext(req.Context())
	userID, err := a.GetUserID(user, onCallPluginSettings)
	if err != nil {
		log.DefaultLogger.Error("Error getting user id: %v", err)
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	log.DefaultLogger.Info(fmt.Sprintf("User %+v, UserID = %s", user, strconv.Itoa(userID)))

	reqURL, err := url.JoinPath(onCallPluginSettings.OnCallAPIURL, "api/internal/v1/", req.URL.Path)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	proxyReq, err := http.NewRequest(proxyMethod, reqURL, bodyReader)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	proxyReq.Header = req.Header
	SetAuthorizationHeader(onCallPluginSettings, proxyReq)

	err = SetXInstanceContextHeader(onCallPluginSettings, proxyReq)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	err = SetXGrafanaContextHeader(user, userID, proxyReq)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	err = a.SetPermissionsHeader(userID, onCallPluginSettings, proxyReq)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	err = a.SetTeamsHeader(userID, onCallPluginSettings, proxyReq)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	if proxyMethod == "POST" || proxyMethod == "PUT" || proxyMethod == "PATCH" {
		proxyReq.Header.Set("Content-Type", "application/json")
	}
	log.DefaultLogger.Info(fmt.Sprintf("Making request to oncall = %+v", onCallPluginSettings))
	res, err := a.httpClient.Do(proxyReq)
	if err != nil {
		log.DefaultLogger.Error(fmt.Sprintf("Error request to oncall = %+v", err))
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	defer res.Body.Close()

	for name, values := range res.Header {
		for _, value := range values {
			w.Header().Add(name, value)
		}
	}
	w.WriteHeader(res.StatusCode)
	io.Copy(w, res.Body)
}

// registerRoutes takes a *http.ServeMux and registers some HTTP handlers.
func (a *App) registerRoutes(mux *http.ServeMux) {
	mux.HandleFunc("/", a.handleOnCall)
}
