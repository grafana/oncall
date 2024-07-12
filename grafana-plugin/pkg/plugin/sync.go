package plugin

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"github.com/grafana/grafana-plugin-sdk-go/backend/log"
	"github.com/yudai/gojsondiff"
	"net/http"
	"net/url"
	"strconv"
	"time"
)

func (a *App) handleSync(w http.ResponseWriter, req *http.Request) {
	waitToCompleteParameter := req.URL.Query().Get("wait")
	var waitToComplete = false
	var err error
	if waitToCompleteParameter != "" {
		waitToComplete, err = strconv.ParseBool(waitToCompleteParameter)
		if err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}
	}

	forceSendParameter := req.URL.Query().Get("force")
	var forceSend = false
	if forceSendParameter != "" {
		forceSend, err = strconv.ParseBool(forceSendParameter)
		if err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}
	}

	if waitToComplete {
		err := a.makeSyncRequest(req.Context(), forceSend)
		if err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}
	} else {
		go func() {
			err := a.makeSyncRequest(req.Context(), forceSend)
			if err != nil {
				log.DefaultLogger.Error("Error making sync request", "error", err)
			}
		}()
	}

	w.WriteHeader(http.StatusOK)
}

func structToMap(obj interface{}) map[string]interface{} {
	var mapResult map[string]interface{}
	jsonBytes, err := json.Marshal(obj)
	if err != nil {
		log.DefaultLogger.Error("error marshalling json: ", "error", err)
		return nil
	}
	err = json.Unmarshal(jsonBytes, &mapResult)
	if err != nil {
		log.DefaultLogger.Error("error unmarshalling json: ", "error", err)
		return nil
	}
	return mapResult
}

func (a *App) getDifferences(newOnCallSync *OnCallSync) gojsondiff.Diff {
	if a.lastOnCallSync == nil {
		log.DefaultLogger.Info("No saved OnCallSync to compare")
		return nil
	}

	last := structToMap(a.lastOnCallSync)
	current := structToMap(newOnCallSync)

	if last == nil || current == nil {
		log.DefaultLogger.Info(fmt.Sprintf("last or current OnCallSync is nil %v, %v", last, current))
		return nil
	}

	differ := gojsondiff.New()
	return differ.CompareObjects(last, current)
}

func (a *App) makeSyncRequest(ctx context.Context, forceSend bool) error {
	startMakeSyncRequest := time.Now()
	defer func() {
		elapsed := time.Since(startMakeSyncRequest)
		log.DefaultLogger.Info("makeSyncRequest", "time", elapsed)
	}()

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

	diff := a.getDifferences(onCallSync)
	if diff != nil && !diff.Modified() && !forceSend {
		log.DefaultLogger.Info("No changes detected to sync")
		return nil
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

	a.lastOnCallSync = onCallSync
	return nil
}
