package plugin

import (
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/google/go-cmp/cmp"
	"github.com/google/go-cmp/cmp/cmpopts"
)

func TestGetPermissionsForUser(t *testing.T) {
	tests := []struct {
		name           string
		user           *OnCallUser
		plugin         *App
		mockResponse   string
		mockStatusCode int
		want           []RBACPermission
		wantErr        bool
	}{
		{
			name: "empty permissions",
			user: &OnCallUser{
				ID: 1,
			},
			plugin: &App{
				pluginIDsToSyncPermissions: []string{},
				httpClient:                 &http.Client{},
				OnCallDebugStats:           &OnCallDebugStats{},
			},
			mockResponse:   `[]`,
			mockStatusCode: http.StatusOK,
			want:           []RBACPermission{},
			wantErr:        false,
		},
		{
			name: "filters out proper permissions",
			user: &OnCallUser{
				ID: 1,
			},
			plugin: &App{
				pluginIDsToSyncPermissions: []string{
					"grafana-oncall-app",
					"grafana-labels-app",
				},
				httpClient:       &http.Client{},
				OnCallDebugStats: &OnCallDebugStats{},
			},
			mockResponse:   `[{"action": "grafana-oncall-app.api-keys:read"}, {"action": "grafana-labels-app.label:write"}, {"action": "grafana-other-app.object:read"}]`,
			mockStatusCode: http.StatusOK,
			want: []RBACPermission{
				{
					Action: "grafana-oncall-app.api-keys:read",
				},
				{
					Action: "grafana-labels-app.label:write",
				},
			},
			wantErr: false,
		},
		{
			name: "error creating URL",
			user: &OnCallUser{
				ID: 1,
			},
			plugin: &App{
				pluginIDsToSyncPermissions: []string{},
				httpClient:                 &http.Client{},
				OnCallDebugStats:           &OnCallDebugStats{},
			},
			mockResponse:   ``,
			mockStatusCode: http.StatusOK,
			want:           nil,
			wantErr:        true,
		},
		{
			name: "error making request",
			user: &OnCallUser{
				ID: 1,
			},
			plugin: &App{
				pluginIDsToSyncPermissions: []string{},
				httpClient:                 &http.Client{},
				OnCallDebugStats:           &OnCallDebugStats{},
			},
			mockResponse:   ``,
			mockStatusCode: http.StatusInternalServerError,
			want:           nil,
			wantErr:        true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create a mock server
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				w.WriteHeader(tt.mockStatusCode)
				w.Write([]byte(tt.mockResponse))
			}))
			defer server.Close()

			settings := &OnCallPluginSettings{
				GrafanaURL:   server.URL,
				GrafanaToken: "token",
			}

			// Override the httpClient with the mock server's client
			tt.plugin.httpClient = server.Client()

			got, err := tt.plugin.GetPermissionsForUser(settings, tt.user)

			if (err != nil) != tt.wantErr {
				t.Errorf("GetPermissionsForUser() error = %v, wantErr %v", err, tt.wantErr)
				return
			}

			if diff := cmp.Diff(tt.want, got, cmpopts.EquateEmpty()); diff != "" {
				t.Errorf("GetPermissionsForUser() mismatch (-want +got):\n%s", diff)
			}
		})
	}
}

func TestGetAllPermissions(t *testing.T) {
	tests := []struct {
		name           string
		plugin         *App
		mockResponses  map[string]string
		mockStatusCode int
		want           map[string]map[string]interface{}
		wantErr        bool
	}{
		{
			name: "empty permissions",
			plugin: &App{
				pluginIDsToSyncPermissions: []string{},
				httpClient:                 &http.Client{},
				OnCallDebugStats:           &OnCallDebugStats{},
			},
			mockResponses:  map[string]string{},
			mockStatusCode: http.StatusOK,
			want:           map[string]map[string]interface{}{},
			wantErr:        false,
		},
		{
			name: "merge permissions from multiple plugins",
			plugin: &App{
				pluginIDsToSyncPermissions: []string{
					"grafana-oncall-app",
					"grafana-labels-app",
				},
				httpClient:       &http.Client{},
				OnCallDebugStats: &OnCallDebugStats{},
			},
			mockResponses: map[string]string{
				"grafana-oncall-app": `{"1": {"grafana-oncall-app.api-keys:read": null}}`,
				"grafana-labels-app": `{"1": {"grafana-labels-app.label:write": null}, "2": {"grafana-labels-app.label:write": null}}`,
			},
			mockStatusCode: http.StatusOK,
			want: map[string]map[string]interface{}{
				"1": {
					"grafana-oncall-app.api-keys:read": nil,
					"grafana-labels-app.label:write":   nil,
				},
				"2": {
					"grafana-labels-app.label:write": nil,
				},
			},
			wantErr: false,
		},
		{
			name: "error getting permissions for a plugin",
			plugin: &App{
				pluginIDsToSyncPermissions: []string{
					"grafana-oncall-app",
				},
				httpClient:       &http.Client{},
				OnCallDebugStats: &OnCallDebugStats{},
			},
			mockResponses:  map[string]string{},
			mockStatusCode: http.StatusInternalServerError,
			want:           nil,
			wantErr:        true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create a mock server
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				pluginId := r.URL.Query().Get("actionPrefix")
				if response, ok := tt.mockResponses[pluginId]; ok {
					w.WriteHeader(tt.mockStatusCode)
					w.Write([]byte(response))
				} else {
					w.WriteHeader(tt.mockStatusCode)
				}
			}))
			defer server.Close()

			settings := &OnCallPluginSettings{
				GrafanaURL:   server.URL,
				GrafanaToken: "token",
			}

			// Override the httpClient with the mock server's client
			tt.plugin.httpClient = server.Client()

			got, err := tt.plugin.GetAllPermissions(settings)

			if (err != nil) != tt.wantErr {
				t.Errorf("GetAllPermissions() error = %v, wantErr %v", err, tt.wantErr)
				return
			}

			if diff := cmp.Diff(tt.want, got, cmpopts.EquateEmpty()); diff != "" {
				t.Errorf("GetAllPermissions() mismatch (-want +got):\n%s", diff)
			}
		})
	}
}
