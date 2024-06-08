package plugin

import (
	"bytes"
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

type OnCallSync struct {
	Users       []OnCallUser  `json:"users"`
	Teams       []OnCallTeam  `json:"teams"`
	TeamMembers map[int][]int `json:"teamMembers"`
}

type responseWriter struct {
	http.ResponseWriter
	statusCode int
	body       bytes.Buffer
}

func (rw *responseWriter) WriteHeader(statusCode int) {
	rw.statusCode = statusCode
	rw.ResponseWriter.WriteHeader(statusCode)
}

func (rw *responseWriter) Write(b []byte) (int, error) {
	if rw.statusCode == 0 {
		rw.WriteHeader(http.StatusOK)
	}
	n, err := rw.body.Write(b)
	if err != nil {
		return n, err
	}
	return rw.ResponseWriter.Write(b)
}

func afterRequest(handler http.Handler, afterFunc func(*responseWriter, *http.Request)) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		wrappedWriter := &responseWriter{ResponseWriter: w}
		handler.ServeHTTP(wrappedWriter, r)
		afterFunc(wrappedWriter, r)
	})
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

func SetOnCallUserHeader(onCallUser *OnCallUser, settings OnCallPluginSettings, req *http.Request) error {
	xOnCallUserHeader, err := json.Marshal(onCallUser)
	if err != nil {
		return err
	}
	req.Header.Set("X-OnCall-User-Context", string(xOnCallUserHeader))
	return nil
}

func (a *App) handleInternalApi(w http.ResponseWriter, req *http.Request) {
	proxyMethod := req.Method
	var bodyReader io.Reader
	if req.Body != nil {
		proxyBody, err := io.ReadAll(req.Body)
		if err != nil {
			log.DefaultLogger.Error("Error reading original request: %v", err)
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}
		if proxyBody != nil {
			bodyReader = bytes.NewReader(proxyBody)
		}
	}

	onCallPluginSettings, err := OnCallSettingsFromContext(req.Context())
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	user := httpadapter.UserFromContext(req.Context())
	onCallUser, err := a.GetUser(&onCallPluginSettings, user)
	if err != nil {
		log.DefaultLogger.Error("Error getting user id: %v", err)
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	reqURL, err := url.JoinPath(onCallPluginSettings.OnCallAPIURL, "api/internal/v1/", req.URL.Path)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	parsedReqURL, err := url.Parse(reqURL)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	parsedReqURL.RawQuery = req.URL.RawQuery

	proxyReq, err := http.NewRequest(proxyMethod, parsedReqURL.String(), bodyReader)
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

	err = SetXGrafanaContextHeader(user, onCallUser.ID, proxyReq)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	err = SetOnCallUserHeader(onCallUser, onCallPluginSettings, proxyReq)
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

func (a *App) handleInstall(w *responseWriter, req *http.Request) {
	var provisioningData OnCallProvisioningJSONData
	err := json.Unmarshal(w.body.Bytes(), &provisioningData)
	if err != nil {
		log.DefaultLogger.Error(fmt.Sprintf("Error unmarshalling OnCallProvisioningJSONData = %+v", err))
		return
	}

	onCallPluginSettings, err := OnCallSettingsFromContext(req.Context())
	if err != nil {
		log.DefaultLogger.Error(fmt.Sprintf("Error getting settings from context = %+v", err))
		return
	}

	log.DefaultLogger.Info(fmt.Sprintf("Settings = %+v", onCallPluginSettings))
	log.DefaultLogger.Info(fmt.Sprintf("Provisioning data = %+v", provisioningData))

	if provisioningData.Error != "" {
		log.DefaultLogger.Error(fmt.Sprintf("Error installing OnCall = %s", provisioningData.Error))
		return
	}
	onCallPluginSettings.License = provisioningData.License
	onCallPluginSettings.OrgID = provisioningData.OrgId
	onCallPluginSettings.StackID = provisioningData.StackId
	onCallPluginSettings.OnCallToken = provisioningData.OnCallToken

	err = a.SaveOnCallSettings(onCallPluginSettings)
	if err != nil {
		log.DefaultLogger.Error(fmt.Sprintf("Error saving settings = %+v", err))
		return
	}
}

func (a *App) handleCurrentUser(w http.ResponseWriter, req *http.Request) {
	onCallPluginSettings, err := OnCallSettingsFromContext(req.Context())
	if err != nil {
		log.DefaultLogger.Error(fmt.Sprintf("Error getting settings from context = %+v", err))
		return
	}

	user := httpadapter.UserFromContext(req.Context())
	onCallUser, err := a.GetUserForHeader(&onCallPluginSettings, user)
	if err != nil {
		log.DefaultLogger.Error(fmt.Sprintf("Error getting user = %+v", err))
		return
	}

	w.Header().Add("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(onCallUser); err != nil {
		http.Error(w, "Failed to encode response", http.StatusInternalServerError)
		return
	}
	w.WriteHeader(http.StatusOK)
}

func (a *App) handleSync(w http.ResponseWriter, req *http.Request) {
	onCallPluginSettings, err := OnCallSettingsFromContext(req.Context())
	if err != nil {
		log.DefaultLogger.Error(fmt.Sprintf("Error getting settings from context = %+v", err))
		return
	}

	onCallSync := OnCallSync{}
	onCallSync.Users, err = a.GetAllUsersWithPermissions(&onCallPluginSettings)
	if err != nil {
		log.DefaultLogger.Error(fmt.Sprintf("Error getting users = %+v", err))
		return
	}

	onCallSync.Teams, err = a.GetAllTeams(&onCallPluginSettings)
	if err != nil {
		log.DefaultLogger.Error(fmt.Sprintf("Error getting teams = %+v", err))
		return
	}

	teamMembers, err := a.GetAllTeamMembers(&onCallPluginSettings, onCallSync.Teams)
	if err != nil {
		log.DefaultLogger.Error(fmt.Sprintf("Error getting team members = %+v", err))
		return
	}
	onCallSync.TeamMembers = teamMembers

	w.Header().Add("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(onCallSync); err != nil {
		http.Error(w, "Failed to encode response", http.StatusInternalServerError)
		return
	}
	w.WriteHeader(http.StatusOK)
}

// registerRoutes takes a *http.ServeMux and registers some HTTP handlers.
func (a *App) registerRoutes(mux *http.ServeMux) {
	mux.Handle("/plugin/self-hosted/install", afterRequest(http.HandlerFunc(a.handleInternalApi), a.handleInstall))
	mux.HandleFunc("/test-current-user", a.handleCurrentUser)
	mux.HandleFunc("/test-sync", a.handleSync)
	mux.HandleFunc("/", a.handleInternalApi)
}
