package plugin

import (
	"bytes"
	"fmt"
	"net/http"
)

// curl -X GET -H "Accept: application/json"  http://oncall:oncall@localhost:3000/api/plugins/grafana-oncall-app/resources/ping | jq
func (a *App) handlePing(w http.ResponseWriter, req *http.Request) {
	w.Header().Add("Content-Type", "application/json")
	
	msg := fmt.Sprintf(`{"message":"%s"}`, "ok")
	if _, err := w.Write([]byte(msg)); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	w.WriteHeader(http.StatusOK)
}

// registerRoutes takes a *http.ServeMux and registers some HTTP handlers.
func (a *App) registerRoutes(mux *http.ServeMux) {
	mux.HandleFunc("/", a.handlePing)
}

// Custom ResponseWriter to capture the response
type capturedResponseWriter struct {
    http.ResponseWriter
    body bytes.Buffer
}

func (w *capturedResponseWriter) Write(b []byte) (int, error) {
    // Write the response to the buffer
    w.body.Write(b)
    // Write the response to the actual ResponseWriter
    return w.ResponseWriter.Write(b)
}