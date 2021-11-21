package helper

import (
	"context"
	"encoding/json"
	"fmt"

	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"sigs.k8s.io/controller-runtime/pkg/client"

	"digi.dev/digi/pkg/core"
	"digi.dev/digi/space"
)

func GetMounts(o *unstructured.Unstructured) (map[string]space.MountRefs, error) {
	rawMounts, ok, err := unstructured.NestedMap(o.Object, space.MountAttrPathSlice...)
	if err != nil {
		return nil, err
	}
	if !ok {
		return nil, nil
	}

	var mounts map[string]space.MountRefs
	mounts = make(map[string]space.MountRefs)

	for n, m := range rawMounts {
		jsonBody, err := json.Marshal(m)
		if err != nil {
			return nil, fmt.Errorf("error marshalling mount references: %v", err)
		}

		var mr space.MountRefs
		if err := json.Unmarshal(jsonBody, &mr); err != nil {
			return nil, fmt.Errorf("error unmarshalling mount references: %v", err)
		}
		mounts[n] = mr
	}

	return mounts, nil
}

func SetMounts(o *unstructured.Unstructured, mts map[string]space.MountRefs) (*unstructured.Unstructured, error) {
	jsonBody, err := json.Marshal(mts)
	if err != nil {
		return nil, err
	}

	var unstructuredMts map[string]interface{}
	if err := json.Unmarshal(jsonBody, &unstructuredMts); err != nil {
		return nil, err
	}

	err = unstructured.SetNestedMap(o.Object, unstructuredMts, space.MountAttrPathSlice...)
	if err != nil {
		return nil, err
	}
	return o, nil
}

func GetObj(c client.Client, ar *core.Auri) (*unstructured.Unstructured, error) {
	obj := &unstructured.Unstructured{}
	obj.SetGroupVersionKind(ar.Gvk())

	if err := c.Get(context.TODO(), ar.SpacedName(), obj); err != nil {
		return nil, err
	}
	return obj, nil
}

func GetAttr(obj *unstructured.Unstructured, path string) (interface{}, error) {
	// XXX check support for dot in the key
	objAttr, ok, err := unstructured.NestedFieldCopy(obj.Object, core.AttrPathSlice(path)...)
	if err != nil {
		return nil, err
	}
	if !ok {
		return nil, fmt.Errorf("unable to find attrs in source given %s", path)
	}
	return objAttr, nil
}
