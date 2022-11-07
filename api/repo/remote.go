package repo

import (
	"fmt"
	"strings"

	"github.com/hashicorp/go-getter"
	"github.com/silveryfu/inflection"

	"digi.dev/digi/pkg/core"
)

// Pull a kind
// TBD support other remote types
func Pull(kind *core.Kind) error {
	// GitHub:
	// Ex. mock.digi.dev/v1/lamps
	// - digi.dev -> org or username
	// - mock -> repository name, need to pluralize
	// - v1 -> version, TBD ignored for now
	// go-getter url: git::https://digi.dev/mock.git//lamp
	var urlStr string
	ss := strings.Split(kind.Group, ".")
	switch len(ss) {
	case 2:
		// Ex. example.com/v1/lamp
		urlStr = fmt.Sprintf("git::https://%s/%s", kind.Group, kind.Name)
	case 3:
		// Ex. mock.digi.dev/v1/lamp
		org, repo := strings.Join(ss[1:], "."), inflection.Plural(ss[0])
		urlStr = fmt.Sprintf("git::https://%s/%s//%s", org, repo, kind.Name)
	default:
		panic("unimplemented")
	}
	err := getter.GetAny(kind.Name, urlStr)
	if err != nil {
		panic(err)
	}

	return nil
}
