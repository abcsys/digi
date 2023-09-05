package api

var version string

func Version() string {
	if version != "" {
		return version
	}
	return "undefined"
}
