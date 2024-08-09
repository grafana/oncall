package plugin

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strconv"

	"github.com/grafana/grafana-plugin-sdk-go/backend"
	"github.com/grafana/grafana-plugin-sdk-go/backend/log"
	"github.com/grafana/grafana-plugin-sdk-go/backend/resource/httpadapter"
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

type OnCallProvisioningJSONData struct {
	Error       string `json:"error,omitempty"`
	StackId     int    `json:"stackId,omitempty"`
	OrgId       int    `json:"orgId,omitempty"`
	OnCallToken string `json:"onCallToken,omitempty"`
	License     string `json:"license,omitempty"`
}

func SetXInstanceContextHeader(settings *OnCallPluginSettings, req *http.Request) error {
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

func SetAuthorizationHeader(settings *OnCallPluginSettings, req *http.Request) {
	req.Header.Set("Authorization", settings.OnCallToken)
}

func SetOnCallUserHeader(onCallUser *OnCallUser, req *http.Request) error {
	xOnCallUserHeader, err := json.Marshal(onCallUser)
	if err != nil {
		return err
	}
	req.Header.Set("X-OnCall-User-Context", string(xOnCallUserHeader))
	return nil
}

func (a *App) SetupRequestHeadersForOnCall(ctx context.Context, settings *OnCallPluginSettings, req *http.Request) error {
	req.Header.Del("Cookie")
	req.Header.Del("Set-Cookie")

	SetAuthorizationHeader(settings, req)

	err := SetXInstanceContextHeader(settings, req)
	if err != nil {
		log.DefaultLogger.Error("Error setting instance header", "error", err)
		return err
	}

	pluginContext := httpadapter.PluginConfigFromContext(ctx)
	req.Header.Set("User-Agent", fmt.Sprintf("GrafanaOnCall/%s", pluginContext.PluginVersion))

	return nil
}

func (a *App) SetupRequestHeadersForOnCallWithUser(ctx context.Context, settings *OnCallPluginSettings, req *http.Request) error {
	err := a.SetupRequestHeadersForOnCall(ctx, settings, req)
	if err != nil {
		return err
	}

	user := httpadapter.UserFromContext(ctx)
	onCallUser, err := a.GetUserForHeader(settings, user)
	if err != nil {
		log.DefaultLogger.Error("Error getting user", "error", err)
		return err
	}

	err = SetXGrafanaContextHeader(user, onCallUser.ID, req)
	if err != nil {
		log.DefaultLogger.Error("Error setting context header", "error", err)
		return err
	}

	err = SetOnCallUserHeader(onCallUser, req)
	if err != nil {
		log.DefaultLogger.Error("Error setting user header", "error", err)
		return err
	}

	return nil
}

func (a *App) ProxyRequestToOnCall(w http.ResponseWriter, req *http.Request, pathPrefix string) {
	proxyMethod := req.Method
	var bodyReader io.Reader
	if req.Body != nil {
		proxyBody, err := io.ReadAll(req.Body)
		if err != nil {
			log.DefaultLogger.Error("Error reading original request", "error", err)
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}
		if proxyBody != nil {
			bodyReader = bytes.NewReader(proxyBody)
		}
	}

	onCallPluginSettings, err := a.OnCallSettingsFromContext(req.Context())
	if err != nil {
		log.DefaultLogger.Error("Error getting plugin settings", "error", err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	reqURL, err := url.JoinPath(onCallPluginSettings.OnCallAPIURL, pathPrefix, req.URL.Path)
	if err != nil {
		log.DefaultLogger.Error("Error joining path", "error", err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	parsedReqURL, err := url.Parse(reqURL)
	if err != nil {
		log.DefaultLogger.Error("Error parsing path", "error", err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	parsedReqURL.RawQuery = req.URL.RawQuery

	proxyReq, err := http.NewRequest(proxyMethod, parsedReqURL.String(), bodyReader)
	if err != nil {
		log.DefaultLogger.Error("Error creating request", "error", err)
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	proxyReq.Header = req.Header
	err = a.SetupRequestHeadersForOnCallWithUser(req.Context(), onCallPluginSettings, proxyReq)
	if err != nil {
		log.DefaultLogger.Error("Error setting up headers", "error", err)
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	if proxyMethod == "POST" || proxyMethod == "PUT" || proxyMethod == "PATCH" {
		proxyReq.Header.Set("Content-Type", "application/json")
	}

	res, err := a.httpClient.Do(proxyReq)
	if err != nil {
		log.DefaultLogger.Error("Error request to oncall", "error", err)
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
