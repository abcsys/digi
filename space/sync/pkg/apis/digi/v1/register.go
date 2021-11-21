// NOTE: Boilerplate only.  Ignore this file.

// Package v1 contains API Schema definitions for the digi v1 API group
// +k8s:deepcopy-gen=package,register
// +groupName=digi.dev
package v1

import (
"k8s.io/apimachinery/pkg/runtime/schema"
"sigs.k8s.io/controller-runtime/pkg/scheme"
)

const (
	group = "digi.dev"
	version = "v1"
	resource = "syncs"
)

var (
	GVR = schema.GroupVersionResource{
		Group:    group,
		Version:  version,
		Resource: resource,
	}

	// SchemeGroupVersion is group version used to register these objects
	SchemeGroupVersion = schema.GroupVersion{Group: group, Version: version}

	// SchemeBuilder is used to add go types to the GroupVersionKind scheme
	SchemeBuilder = &scheme.Builder{GroupVersion: SchemeGroupVersion}
)
