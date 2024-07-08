package plugin

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"github.com/grafana/grafana-plugin-sdk-go/backend/log"
	"github.com/grafana/grafana-plugin-sdk-go/backend/resource/httpadapter"
	"net/url"
	"time"

	"net/http"
)

func (a *App) handleSync(w http.ResponseWriter, req *http.Request) {
	err := a.makeSyncRequest(req.Context())
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	w.WriteHeader(http.StatusOK)
}

func (a *App) makeSyncRequest(ctx context.Context) error {
	log.DefaultLogger.Info("Start makeSyncRequest")

	onCallPluginSettings, err := a.OnCallSettingsFromContext(ctx)
	if err != nil {
		return fmt.Errorf("error getting settings from context: %v ", err)
	}

	onCallSync, err := a.GetSyncData(ctx, onCallPluginSettings)
	if err != nil {
		return fmt.Errorf("error getting sync data: %v", err)
	}

	onCallSyncJsonData, err := json.Marshal(onCallSync)
	if err != nil {
		return fmt.Errorf("error marshalling JSON: %v", err)
	}

	syncURL, err := url.JoinPath(onCallPluginSettings.OnCallAPIURL, "api/internal/v1/plugin/v2/sync")
	if err != nil {
		return fmt.Errorf("error joining path: %v", err)
	}

	parsedSyncURL, err := url.Parse(syncURL)
	if err != nil {
		return fmt.Errorf("error parsing path: %v", err)
	}

	syncReq, err := http.NewRequest("POST", parsedSyncURL.String(), bytes.NewBuffer(onCallSyncJsonData))
	if err != nil {
		return fmt.Errorf("error creating request: ", err)
	}
	syncReq.Header.Set("Content-Type", "application/json")

	res, err := a.httpClient.Do(syncReq)
	if err != nil {
		return fmt.Errorf("error request to oncall: ", err)
	}
	defer res.Body.Close()

	log.DefaultLogger.Info("Finish makeSyncRequest")
	return nil
}

func (a *App) startSyncProcess(ctx context.Context) {
	log.DefaultLogger.Info("Start startSyncProcess")
	ticker := time.NewTicker(60 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			go func() {
				log.DefaultLogger.Info(fmt.Sprintf("ctx1: %+v", ctx))
				ctx2 := context.Background()

				log.DefaultLogger.Info(fmt.Sprintf("ctx2: %+v", ctx2))
				pluginCtx := httpadapter.PluginConfigFromContext(ctx2)
				log.DefaultLogger.Info(fmt.Sprintf("pluginCtx: %+v", pluginCtx))

				err := a.makeSyncRequest(ctx2)
				if err != nil {
					log.DefaultLogger.Error("error making sync request: ", err)
				}
			}()
		}
	}
}
