package api

import (
	"encoding/json"
	"fmt"
	_ "log"
	"strings"

	"github.com/tidwall/sjson"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"

	"digi.dev/digi/space"
)

const (
	MOUNT = iota
	UNMOUNT
	YIELD
	ACTIVATE // unyield
)

// Mounter contains methods to perform a mount
type Mounter struct {
	space.Mount
	Op int
}

func NewMounter(s, t, mode string) (*Mounter, error) {
	si, err := ParseAuri(s)
	if err != nil {
		return nil, err
	}

	ti, err := ParseAuri(t)
	if err != nil {
		return nil, err
	}

	return &Mounter{
		Mount:
		space.Mount{
			Source: si,
			Target: ti,
			Mode:   mode,
			Status: space.MountActiveStatus,
		},
	}, nil
}

func (m *Mounter) Do() error {
	c, err := NewClient()
	if err != nil {
		return fmt.Errorf("unable to create k8s client: %v", err)
	}

	// source digivice
	_, err = c.GetResourceJson(&m.Source)
	if err != nil {
		return fmt.Errorf("%v", err)
	}

	// target digivice
	tj, err := c.GetResourceJson(&m.Target)
	if err != nil {
		return fmt.Errorf("%v", err)
	}


	var pathPrefix []string
	pathPrefix = append(space.MountAttrPathSlice, []string{
		m.Source.Kind.GvrString(),
		m.Source.SpacedName().String(),
	}...)

	// XXX use the path slice and unstructured in lieu of sjson
	var pathPrefixStr string
	pathPrefixStr = fmt.Sprintf("%s%c%s%c%s",
		strings.TrimLeft(space.MountAttrPath, "."),
		'.', m.Source.Kind.EscapedGvrString(),
		'.', m.Source.SpacedName().String())

	switch m.Op {
	case MOUNT:
		// updates the target digivice's model with a mount reference to the source digivice;
		// a mount is successful iff 1. source and target are compatible; 2. caller has sufficient
		// access rights.
		var modePath, statusPath string
		modePath = pathPrefixStr + space.MountModeAttrPath
		statusPath = pathPrefixStr + space.MountStatusAttrPath

		// set mode and status
		// XXX replace sjson with unstructured.unstructured
		tj, err := sjson.SetRaw(tj, modePath, "\""+m.Mode+"\"")
		if err != nil {
			return fmt.Errorf("unable to merge json: %v", err)
		}

		tj, err = sjson.SetRaw(tj, statusPath, "\""+m.Status+"\"")
		if err != nil {
			return fmt.Errorf("unable to merge json: %v", err)
		}
		//log.Printf("mount: %v", tj)

		return c.UpdateFromJson(tj)

	case UNMOUNT:
		if ok, err := m.mountExists(tj, pathPrefix); err != nil || !ok {
			return fmt.Errorf("unable to find mount %s in %s: %v", pathPrefix, m.Target.SpacedName(), err)
		}

		// now remove it
		tj, err := sjson.Delete(tj, pathPrefixStr)
		if err != nil {
			return err
		}
		return c.UpdateFromJson(tj)

	case YIELD:
		if ok, err := m.mountExists(tj, pathPrefix); err != nil || !ok {
			return fmt.Errorf("unable to find mount %s in %s: %v", pathPrefix, m.Target.SpacedName(), err)
		}

		// update its status
		var statusPath string
		statusPath = pathPrefixStr + space.MountStatusAttrPath

		m.Status = space.MountInactiveStatus
		tj, err = sjson.SetRaw(tj, statusPath, "\""+m.Status+"\"")
		if err != nil {
			return fmt.Errorf("unable to merge json: %v", err)
		}
		return c.UpdateFromJson(tj)

	case ACTIVATE:
		if ok, err := m.mountExists(tj, pathPrefix); err != nil || !ok {
			return fmt.Errorf("unable to find mount %s in %s: %v", pathPrefix, m.Target.SpacedName(), err)
		}

		statusPath := pathPrefixStr + space.MountStatusAttrPath

		m.Status = space.MountActiveStatus
		tj, err = sjson.SetRaw(tj, statusPath, "\""+m.Status+"\"")
		if err != nil {
			return fmt.Errorf("unable to merge json: %v", err)
		}
		return c.UpdateFromJson(tj)

	default:
		return fmt.Errorf("unrecognized mount mode")
	}
}

func (m *Mounter) mountExists(j string, path []string) (bool, error) {
	var obj map[string]interface{}
	if err := json.Unmarshal([]byte(j), &obj); err != nil {
		return false, err
	}

	// TBD leaf attr throws an error
	_, ok, err := unstructured.NestedMap(obj, path...)
	if err != nil {
		return false, err
	}
	if !ok {
		return false, nil
	}

	return ok, err
}
