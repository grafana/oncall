package plugin

import (
	"net/http"
)

type OnCallInstall struct {
	OnCallError `json:"onCallError,omitempty"`
}

func (a *App) handleInstall(w http.ResponseWriter, req *http.Request) {

}
