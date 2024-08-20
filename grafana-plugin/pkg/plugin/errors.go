package plugin

const (
	INSTALL_ERROR_CODE = 1000
)

type OnCallError struct {
	Code    int                 `json:"code"`
	Message string              `json:"message"`
	Fields  map[string][]string `json:"fields,omitempty"`
}
