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
	IsAnonymous bool   `json:"IsAnonymous"`
	Name        string `json:"Name"`
	Login       string `json:"Login"`
	Email       string `json:"Email"`
	Role        string `json:"Role"`
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

func SetXGrafanaContextHeader(user *backend.User, req *http.Request) error {
	var xGrafanaContext XGrafanaContextJSONData
	if user == nil {
		xGrafanaContext = XGrafanaContextJSONData{
			IsAnonymous: true,
		}
	} else {
		xGrafanaContext = XGrafanaContextJSONData{
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
	log.DefaultLogger.Info(fmt.Sprintf("User %+v", user))

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

	err = SetXGrafanaContextHeader(user, proxyReq)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	if proxyMethod == "POST" || proxyMethod == "PUT" {
		proxyReq.Header.Set("Content-Type", "application/json")
	}
	res, err := a.httpClient.Do(proxyReq)
	if err != nil {
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
