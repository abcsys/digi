package helper

import (
	"context"
	"fmt"

	"digi.dev/digi/pkg/core"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

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
