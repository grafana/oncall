package plugin

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strconv"

	"github.com/grafana/grafana-plugin-sdk-go/backend/log"

	"github.com/grafana/grafana-plugin-sdk-go/backend"
)

// curl -X GET -H "Accept: application/json"  http://oncall:oncall@localhost:3000/api/plugins/grafana-oncall-app/resources/ping | jq

// handlePing is an example HTTP GET resource that returns a {"message": "ok"} JSON response.
func (a *App) handlePing(w http.ResponseWriter, req *http.Request) {
	w.Header().Add("Content-Type", "application/json")

	cfg := backend.GrafanaConfigFromContext(req.Context())
	saToken, err := cfg.PluginAppClientSecret()
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	msg := fmt.Sprintf(`{"message":  "%s"}`, saToken)
	if _, err := w.Write([]byte(msg)); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	w.WriteHeader(http.StatusOK)
}

// handleEcho is an example HTTP POST resource that accepts a JSON with a "message" key and
// returns to the client whatever it is sent.
func (a *App) handleEcho(w http.ResponseWriter, req *http.Request) {
	if req.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	var body struct {
		Message string `json:"message"`
	}
	if err := json.NewDecoder(req.Body).Decode(&body); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	w.Header().Add("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(body); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	w.WriteHeader(http.StatusOK)
}

// registerRoutes takes a *http.ServeMux and registers some HTTP handlers.
func (a *App) registerRoutes(mux *http.ServeMux) {
	proxyHandler := func(w http.ResponseWriter, r *http.Request) {
		cfg := backend.GrafanaConfigFromContext(r.Context())
		saToken, err := cfg.PluginAppClientSecret()

		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}		

		// Unmarshal JSON data into a map[string]interface{}
		var jsonDataMap map[string]interface{}
		jsonErr := json.Unmarshal(a.settings.JSONData, &jsonDataMap)
		if jsonErr != nil {
			log.DefaultLogger.Info("Errorrrrrr: ", jsonErr)
			return
		}
		log.DefaultLogger.Info("jsonDataMap: ", jsonDataMap)

		stackId := strconv.Itoa(int(jsonDataMap["stackId"].(float64)))
		orgId := strconv.Itoa(int(jsonDataMap["orgId"].(float64)))

		r.Header.Set("X-Instance-Context", "{ \"stack_id\": " + stackId + ", \"org_id\": " + orgId + ", \"grafana_token\": \"" + saToken + "\"}")
		log.DefaultLogger.Info("AppInstanceSettings", a.settings.DecryptedSecureJSONData["onCallApiToken"])
		r.Header.Set("Authorization", a.settings.DecryptedSecureJSONData["onCallApiToken"])

		// Create an HTTP client
        client := &http.Client{}
		targetURL := "http://oncall-dev-engine:8080/api/internal/v1" + r.URL.Path

        // Create a new request
        req, err := http.NewRequest(r.Method, targetURL, r.Body)
        if err != nil {
            log.DefaultLogger.Info("Error creating request:", err)
            http.Error(w, "Internal Server Error", http.StatusInternalServerError)
            return
        }

		log.DefaultLogger.Info("HEADERSSS", r.Header.Get("Authorization"))

		req.Header = r.Header

		// Send the request
        resp, err := client.Do(req)
        if err != nil {
            log.DefaultLogger.Info("Error sending request:", err)
            http.Error(w, "Internal Server Error", http.StatusInternalServerError)
            return
        }
        defer resp.Body.Close()

        // Print the response status code
        log.DefaultLogger.Info("Response status code:", resp.StatusCode)

        // Print the response body
        // Note: You may want to limit the size of the response body to avoid printing large responses
        // For simplicity, this example reads the entire response body into memory
        responseBody, err := io.ReadAll(resp.Body)
        if err != nil {
            log.DefaultLogger.Info("Error reading response body:", err)
            http.Error(w, "Internal Server Error", http.StatusInternalServerError)
            return
        }
        log.DefaultLogger.Info("Response body:", string(responseBody))

        // Forward the response to the original client
        // You may need to copy headers and status code as well if needed
        w.WriteHeader(resp.StatusCode)
        w.Write(responseBody)


		// Define the target URL where you want to proxy the request
		// targetURL, _ := url.Parse("http://localhost:8080/api/internal/v1" + r.URL.Path)

		// log.DefaultLogger.Info("TARGET_URL: ", targetURL.String())

		// // Create a custom ResponseWriter to capture the response
        // capturedResponseWriter := &capturedResponseWriter{ResponseWriter: w}

		// // Create a reverse proxy instance with the target URL
		// proxy := httputil.NewSingleHostReverseProxy(targetURL)

		// // Serve the request by proxying it to the target server
		// proxy.ServeHTTP(w, r)

		// log.DefaultLogger.Info("Response from upstream server: ", string(capturedResponseWriter.body.Bytes()))
	}

	mux.HandleFunc("/", proxyHandler)
	// mux.HandleFunc("/echo", a.handleEcho)
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