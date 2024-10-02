package plugin

import (
	"bytes"
	"compress/gzip"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strconv"
	"sync"
	"time"

	"github.com/grafana/grafana-plugin-sdk-go/backend/log"
)

type OnCallSyncCache struct {
	syncMutex      sync.Mutex
	timer          *time.Timer
	lastOnCallSync *OnCallSync
	start          time.Time
}

type SyncCacheAlreadyLocked struct {
	Message string
}

func (e *SyncCacheAlreadyLocked) Error() string {
	return e.Message
}

func (oc *OnCallSyncCache) UnlockAfterDelay(delay time.Duration) {
	oc.timer = time.AfterFunc(delay, func() {
		oc.syncMutex.Unlock()
		log.DefaultLogger.Info("released OnCallSyncCache lock")
	})
}

func (a *App) HandleSync(w http.ResponseWriter, req *http.Request) {
	if req.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

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
		a.doSync(req.Context(), forceSend)
	}

	w.WriteHeader(http.StatusOK)
}

func (a *App) doSync(ctx context.Context, forceSend bool) {
	go func() {
		err := a.makeSyncRequest(ctx, forceSend)
		var cacheAlreadyLocked *SyncCacheAlreadyLocked
		if errors.As(err, &cacheAlreadyLocked) {
			log.DefaultLogger.Info("Skipping sync", "message", err)
		} else if err != nil {
			log.DefaultLogger.Error("Error making sync request", "error", err)
		}
	}()
}

func (a *App) compareSyncData(newOnCallSync *OnCallSync) bool {
	if a.lastOnCallSync == nil {
		log.DefaultLogger.Info("No saved OnCallSync to compare")
		return false
	}
	return newOnCallSync.Equal(a.lastOnCallSync)
}

func (a *App) makeSyncRequest(ctx context.Context, forceSend bool) error {
	startMakeSyncRequest := time.Now()
	defer func() {
		elapsed := time.Since(startMakeSyncRequest)
		log.DefaultLogger.Info("makeSyncRequest", "time", elapsed.Milliseconds())
	}()

	locked := a.syncMutex.TryLock()
	const duration = 5 * 60 * time.Second
	if !locked {
		elapsed := time.Since(a.start)
		remaining := duration - elapsed
		msg := fmt.Sprintf("sync already in progress, OnCallSyncCache is locked, remaining time  %.0fs", remaining.Seconds())
		return &SyncCacheAlreadyLocked{Message: msg}
	}

	defer a.UnlockAfterDelay(duration)
	a.start = time.Now()

	onCallPluginSettings, err := a.OnCallSettingsFromContext(ctx)
	if err != nil {
		return fmt.Errorf("error getting settings from context: %v ", err)
	}

	onCallSync, err := a.GetSyncData(onCallPluginSettings)
	if err != nil {
		return fmt.Errorf("error getting sync data: %v", err)
	}

	same := a.compareSyncData(onCallSync)
	if same && !forceSend {
		log.DefaultLogger.Info("No changes detected to sync")
		return nil
	}

	onCallSyncJsonData, err := json.Marshal(onCallSync)
	if err != nil {
		return fmt.Errorf("error marshalling JSON: %v", err)
	}

	var syncDataBuffer bytes.Buffer
	gzipWriter := gzip.NewWriter(&syncDataBuffer)
	_, err = gzipWriter.Write(onCallSyncJsonData)
	if err != nil {
		return fmt.Errorf("error writing sync data to gzip writer: %v", err)
	}
	if err := gzipWriter.Close(); err != nil {
		return fmt.Errorf("error closing gzip writer: %v", err)
	}

	syncURL, err := url.JoinPath(onCallPluginSettings.OnCallAPIURL, "api/internal/v1/plugin/v2/sync")
	if err != nil {
		return fmt.Errorf("error joining path: %v", err)
	}

	parsedSyncURL, err := url.Parse(syncURL)
	if err != nil {
		return fmt.Errorf("error parsing path: %v", err)
	}

	syncReq, err := http.NewRequest("POST", parsedSyncURL.String(), &syncDataBuffer)
	if err != nil {
		return fmt.Errorf("error creating request: %v", err)
	}

	err = a.SetupRequestHeadersForOnCall(ctx, onCallPluginSettings, syncReq)
	if err != nil {
		return err
	}
	syncReq.Header.Set("Content-Type", "application/json")
	syncReq.Header.Set("Content-Encoding", "gzip")

	res, err := a.httpClient.Do(syncReq)
	if err != nil {
		return fmt.Errorf("error request to oncall: %v", err)
	}
	defer res.Body.Close()

	if res.StatusCode != http.StatusOK {
		bodyBytes, err := io.ReadAll(res.Body)
		if err != nil {
			log.DefaultLogger.Error("failed to read response body", "error", err, "status", res.StatusCode)
		} else {
			log.DefaultLogger.Error("sync not ok", "status", res.StatusCode, "message", string(bodyBytes))
		}
	} else {
		log.DefaultLogger.Info("sync ok", "status", res.StatusCode)
	}

	a.lastOnCallSync = onCallSync
	return nil
}
