package core

import (
	"fmt"
	"strings"

	"digi.dev/digi/api/alias"
	"digi.dev/digi/pkg/core"
)

// ParseAuri returns an Auri from a slash separated string.
// The following string formats are allowed:
//  1. /group/ver/schema_name/namespace/name.[];
//  2. /group/ver/schema_name/name.[] (use default namespace);
//  3. /namespace/name.[];
//  4. /name.[] (use alias);
//  5. name.[] (use alias);
//
// .[]: model attributes
func ParseAuri(s string) (core.Auri, error) {
	ss := strings.Split(s, fmt.Sprintf("%c", core.UriSeparator))

	splitAttr := func(s string) []string {
		return strings.Split(s, fmt.Sprintf("%c", core.AttrPathSeparator))
	}

	fromAlias := func(s string) (core.Auri, error) {
		ss := splitAttr(s)
		auri, err := alias.Resolve(ss[0])
		if err != nil {
			return core.Auri{}, err
		}
		if len(ss) > 1 {
			auri.Path = strings.Join(ss[1:], fmt.Sprintf("%c", core.AttrPathSeparator))
		}
		return *auri, nil
	}

	var g, v, kn, ns, n, path, other string
	switch len(ss) {
	case 6:
		g, v, kn, ns, other = ss[1], ss[2], ss[3], ss[4], ss[5]
	case 5:
		g, v, kn, ns, other = ss[1], ss[2], ss[3], core.DefaultNamespace, ss[4]
	case 3:
		return core.Auri{}, fmt.Errorf("unimplemented")
	case 2:
		return fromAlias(ss[1])
	case 1:
		return fromAlias(ss[0])
	default:
		return core.Auri{}, fmt.Errorf("auri needs to have either 5, 2, or 1 fields, "+
			"given %d in %s; each field starts with a '/' except for single "+
			"name on default namespace", len(ss)-1, s)
	}

	ss = splitAttr(other)
	if len(ss) > 1 {
		n = ss[0]
		path = strings.Join(ss[1:], fmt.Sprintf("%c", core.AttrPathSeparator))
	} else {
		n = other
		path = ""
	}

	return core.Auri{
		Kind: core.Kind{
			Group:   g,
			Version: v,
			Name:    kn,
		},
		Namespace: ns,
		Name:      n,
		Path:      path,
	}, nil
}
