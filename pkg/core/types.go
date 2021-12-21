package core

import (
	"errors"
	"fmt"
	"regexp"
	"strings"

	"github.com/silveryfu/inflection"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/apimachinery/pkg/types"
)

const (
	DefaultNamespace = "default"

	UriSeparator      = types.Separator
	AttrPathSeparator = '.'
)

var (
	ErrInvalidKind = errors.New("cannot parse kind string")
)

// Kind identifies a model schema, e.g., digi.dev/v1/Lamp; it is a re-declaration of
// https://godoc.org/k8s.io/apimachinery/pkg/runtime/schema#GroupVersionResource with json tags and field name changes.
type Kind struct {
	// Model schema group
	Group string `json:"group,omitempty"`
	// Schema version
	Version string `json:"version,omitempty"`
	// Schema name; first letter capitalized, e.g., Roomba
	Name string `json:"name,omitempty"`
}

func (k *Kind) Plural() string {
	return inflection.Plural(strings.ToLower(k.Name))
}

func (k *Kind) Gvk() schema.GroupVersionKind {
	return schema.GroupVersionKind{
		Group:   k.Group,
		Version: k.Version,
		Kind:    k.Name,
	}
}

func (k *Kind) Gvr() schema.GroupVersionResource {
	return schema.GroupVersionResource{
		Group:    k.Group,
		Version:  k.Version,
		Resource: k.Plural(),
	}
}

func (k *Kind) String() string {
	return fmt.Sprintf("%c%s%c%s%c%s", UriSeparator, k.Group, UriSeparator, k.Version, UriSeparator, k.Name)
}

func (k *Kind) EscapedString() string {
	return fmt.Sprintf("%s%c%s%c%s", regexp.QuoteMeta(k.Group), UriSeparator, regexp.QuoteMeta(k.Version), UriSeparator, k.Name)
}

func (k *Kind) GvrString() string {
	return fmt.Sprintf("%s%c%s%c%s", k.Group, UriSeparator, k.Version, UriSeparator, k.Plural())
}

func (k *Kind) EscapedGvrString() string {
	return regexp.QuoteMeta(k.GvrString())
}

func KindFromString(s string) (*Kind, error) {
	s = strings.Trim(s, "/")
	segs := strings.Split(s, "/")
	if len(segs) != 3 {
		return nil, ErrInvalidKind
	} else {
		return &Kind{
			Group:   segs[0],
			Version: segs[1],
			Name:    segs[2],
		}, nil
	}
}

// Auri identifies a model or its attributes when a path is given
type Auri struct {
	// model schema
	Kind Kind `json:"kind,omitempty"`

	// name of the model
	Name string `json:"name,omitempty"`

	// namespace of the model
	Namespace string `json:"namespace,omitempty"`

	// path to attribute(s) in the model; if path empty, Auri points to the model
	Path string `json:"path,omitempty"`
}

func (ar *Auri) Gvr() schema.GroupVersionResource {
	return ar.Kind.Gvr()
}

func (ar *Auri) Gvk() schema.GroupVersionKind {
	return ar.Kind.Gvk()
}

func (ar *Auri) SpacedName() types.NamespacedName {
	return types.NamespacedName{
		Name:      ar.Name,
		Namespace: ar.Namespace,
	}
}

func (ar *Auri) String() string {
	if ar.Path == "" {
		return fmt.Sprintf("%s%c%s", ar.Kind.String(), UriSeparator, ar.SpacedName().String())
	}
	return fmt.Sprintf("%s%c%s%c%s", ar.Kind.String(), UriSeparator, ar.SpacedName().String(),
		AttrPathSeparator, strings.TrimLeft(ar.Path, fmt.Sprintf("%c", AttrPathSeparator)))
}

func AttrPathSlice(p string) []string {
	sep := fmt.Sprintf("%c", AttrPathSeparator)
	// leading dots in the attribute path is optional
	return strings.Split(strings.TrimLeft(p, sep), sep)
}
