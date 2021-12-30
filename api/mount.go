package api

import (
	"encoding/json"
	"fmt"
	"strings"

	"digi.dev/digi/space"
	"github.com/tidwall/sjson"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
)

const (
	MOUNT = iota
	UNMOUNT
	YIELD
	ACTIVATE
)

// Mounter contains methods to mount one or multiple digis
// to the target digi
type Mounter struct {
	Mounts []*space.Mount
	Op     int
}

func NewMounter(sourceNames []string, targetName string, op int, mode string) (*Mounter, error) {
	var mounts []*space.Mount
	target, err := ParseAuri(targetName)
	if err != nil {
		return nil, err
	}
	for _, name := range sourceNames {
		source, err := ParseAuri(name)
		if err != nil {
			return nil, err
		}
		mounts = append(mounts, &space.Mount{
			Source: source,
			Target: target,
			Mode:   mode,
			Status: space.MountActiveStatus,
		})
	}

	return &Mounter{
		Mounts: mounts,
		Op:     op,
	}, nil
}

func (m *Mounter) Do() error {
	c, err := NewClient()
	if err != nil {
		return fmt.Errorf("unable to create k8s client: %v", err)
	}

	tj, err := c.GetResourceJson(&m.Mounts[0].Target)
	if err != nil {
		return fmt.Errorf("%v", err)
	}

	for _, mount := range m.Mounts {
		// XXX parallelize source pre-check or remove
		//_, err = c.GetResourceJson(&mount.Source)
		//if err != nil {
		//	return fmt.Errorf("%v", err)
		//}

		var pathPrefix []string
		pathPrefix = append(space.MountAttrPathSlice, []string{
			mount.Source.Kind.GvrString(),
			mount.Source.SpacedName().String(),
		}...)

		// TBD use the path slice and unstructured
		var pathPrefixStr string
		pathPrefixStr = fmt.Sprintf("%s%c%s%c%s",
			strings.TrimLeft(space.MountAttrPath, "."),
			'.', mount.Source.Kind.EscapedGvrString(),
			'.', mount.Source.SpacedName().String())

		switch m.Op {
		case MOUNT:
			// updates the target digi's model with a mount reference to the source digivice;
			// a mount is successful iff 1. source and target are compatible; 2. caller has sufficient
			// access rights.
			var modePath, statusPath string
			modePath = pathPrefixStr + space.MountModeAttrPath
			statusPath = pathPrefixStr + space.MountStatusAttrPath

			// XXX replace sjson with unstructured.unstructured
			tj, err = sjson.SetRaw(tj, modePath, "\""+mount.Mode+"\"")
			if err != nil {
				return fmt.Errorf("unable to merge json: %v", err)
			}

			tj, err = sjson.SetRaw(tj, statusPath, "\""+mount.Status+"\"")
			if err != nil {
				return fmt.Errorf("unable to merge json: %v", err)
			}
		case UNMOUNT:
			if ok, err := m.mountExists(tj, pathPrefix); err != nil || !ok {
				return fmt.Errorf("unable to find mount %s in %s: %v", pathPrefix, mount.Target.SpacedName(), err)
			}

			// now remove it
			tj, err = sjson.Delete(tj, pathPrefixStr)
			if err != nil {
				return err
			}
		case YIELD:
			if ok, err := m.mountExists(tj, pathPrefix); err != nil || !ok {
				return fmt.Errorf("unable to find mount %s in %s: %v", pathPrefix, mount.Target.SpacedName(), err)
			}

			// update its status
			var statusPath string
			statusPath = pathPrefixStr + space.MountStatusAttrPath

			mount.Status = space.MountInactiveStatus
			tj, err = sjson.SetRaw(tj, statusPath, "\""+mount.Status+"\"")
			if err != nil {
				return fmt.Errorf("unable to merge json: %v", err)
			}
		case ACTIVATE:
			if ok, err := m.mountExists(tj, pathPrefix); err != nil || !ok {
				return fmt.Errorf("unable to find mount %s in %s: %v", pathPrefix, mount.Target.SpacedName(), err)
			}

			statusPath := pathPrefixStr + space.MountStatusAttrPath

			mount.Status = space.MountActiveStatus
			tj, err = sjson.SetRaw(tj, statusPath, "\""+mount.Status+"\"")
			if err != nil {
				return fmt.Errorf("unable to merge json: %v", err)
			}
		default:
			return fmt.Errorf("unrecognized mount mode")
		}
	}
	return c.UpdateFromJson(tj)
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
