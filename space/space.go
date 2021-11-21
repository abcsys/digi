package space

import (
	"digi.dev/digi/pkg/core"
)

const (
	MountAttrPath = ".spec.mount"

	MountModeAttrPath = ".mode"
	DefaultMountMode  = "hide"

	MountStatusAttrPath = ".status"
	MountActiveStatus   = "active"
	MountInactiveStatus = "inactive"
)

var (
	MountAttrPathSlice = core.AttrPathSlice(MountAttrPath)
	_                  = MountAttrPathSlice
)

// Mount reference
type Mount struct {
	Source core.Auri `json:"source,omitempty"`
	Target core.Auri `json:"target,omitempty"`

	Mode   string `json:"mode,omitempty"`
	Status string `json:"status,omitempty"`
}

// mounts indexed by the target's namespaced name
type MountRefs map[string]*Mount
