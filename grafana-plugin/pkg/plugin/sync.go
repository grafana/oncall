package plugin

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"github.com/grafana/grafana-plugin-sdk-go/backend/log"
	"net/http"
	"net/url"
	"strconv"
)

func (a *App) handleSync(w http.ResponseWriter, req *http.Request) {
	waitToCompleteParameter := req.URL.Query().Get("wait")
	var waitToComplete bool
	var err error
	if waitToCompleteParameter == "" {
		waitToComplete = false
	} else {
		waitToComplete, err = strconv.ParseBool(waitToCompleteParameter)
		if err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}
	}

	if waitToComplete {
		err := a.makeSyncRequest(req.Context())
		if err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}
	} else {
		go func() {
			err := a.makeSyncRequest(req.Context())
			if err != nil {
				log.DefaultLogger.Error("Error making sync request", "error", err)
			}
		}()
	}

	w.WriteHeader(http.StatusOK)
}

func (a *App) makeSyncRequest(ctx context.Context) error {
	log.DefaultLogger.Info("Start makeSyncRequest")
	locked := a.syncMutex.TryLock()
	if !locked {
		return errors.New("sync already in progress")
	}
	defer a.syncMutex.Unlock()

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
		return fmt.Errorf("error creating request: %v", err)
	}

	err = a.SetupRequestHeadersForOnCall(ctx, onCallPluginSettings, syncReq)
	if err != nil {
		return err
	}
	syncReq.Header.Set("Content-Type", "application/json")

	res, err := a.httpClient.Do(syncReq)
	if err != nil {
		return fmt.Errorf("error request to oncall: %v", err)
	}
	defer res.Body.Close()

	log.DefaultLogger.Info("Finish makeSyncRequest")
	return nil
}
