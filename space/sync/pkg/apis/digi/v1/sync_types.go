package v1

import (
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"

	"digi.dev/digi/pkg/core"
)

const (
	SyncMode  = "sync"
	MatchMode = "match"
)

// SyncSpec defines the desired state of Sync
type SyncSpec struct {
	Source core.Auri `json:"source,omitempty"`
	Target core.Auri `json:"target,omitempty"`
	Mode   string    `json:"mode,omitempty"`
}

// SyncStatus defines the observed state of Sync
type SyncStatus struct {
	Done bool `json:"done,omitempty"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// Sync is the Schema for the syncs API
// +kubebuilder:subresource:status
// +kubebuilder:resource:path=syncs,scope=Namespaced
type Sync struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   SyncSpec   `json:"spec,omitempty"`
	Status SyncStatus `json:"status,omitempty"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// SyncList contains a list of Sync
type SyncList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []Sync `json:"items"`
}

func init() {
	SchemeBuilder.Register(&Sync{}, &SyncList{})
}
