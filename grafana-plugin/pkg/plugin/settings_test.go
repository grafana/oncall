package plugin

import (
	"testing"
)

func TestDetermineAndSetLicenseFromVersion(t *testing.T) {
	tests := []struct {
		name        string
		settings    *OnCallPluginSettings
		version     string
		wantLicense string
		wantErr     bool
	}{
		{
			name:        "Empty license with OSS version",
			settings:    &OnCallPluginSettings{},
			version:     "1.2.3",
			wantLicense: OPEN_SOURCE_LICENSE_NAME,
			wantErr:     false,
		},
		{
			name:        "Empty license with cloud version",
			settings:    &OnCallPluginSettings{},
			version:     "v1.2.3",
			wantLicense: CLOUD_LICENSE_NAME,
			wantErr:     false,
		},
		{
			name:        "Empty license with invalid version",
			settings:    &OnCallPluginSettings{},
			version:     "invalid-version",
			wantLicense: "",
			wantErr:     true,
		},
		{
			name:        "Existing license should not change",
			settings:    &OnCallPluginSettings{License: "ExistingLicense"},
			version:     "1.2.3",
			wantLicense: "ExistingLicense",
			wantErr:     false,
		},
		{
			name:        "Cloud app version dev irm pattern",
			settings:    &OnCallPluginSettings{},
			version:     "grafana-irm-app-v2.3.4-5678-xyz",
			wantLicense: CLOUD_LICENSE_NAME,
			wantErr:     false,
		},
		{
			name:        "Cloud app version dev oncall pattern",
			settings:    &OnCallPluginSettings{},
			version:     "grafana-oncall-app-v3.4.5-91011-uvw",
			wantLicense: CLOUD_LICENSE_NAME,
			wantErr:     false,
		},
		{
			name:        "Cloud app version dev pattern points to tagged commit",
			settings:    &OnCallPluginSettings{},
			version:     "grafana-oncall-app-v3.4.5",
			wantLicense: CLOUD_LICENSE_NAME,
			wantErr:     false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := determineAndSetLicenseFromVersion(tt.settings, tt.version)

			if (err != nil) != tt.wantErr {
				t.Errorf("determineAndSetLicenseFromVersion() error = %v, wantErr %v", err, tt.wantErr)
			}

			if tt.settings.License != tt.wantLicense {
				t.Errorf("determineAndSetLicenseFromVersion() got license = %v, want %v", tt.settings.License, tt.wantLicense)
			}
		})
	}
}
