package v1

import (
	"digi.dev/digi/pkg/core"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// YieldPolicySpec defines a pair wise yield policy
type YieldPolicySpec struct {
	Source core.Auri `json:"source,omitempty"`
	Target core.Auri `json:"target,omitempty"`
	// Yield condition, e.g., a jq statement
	Condition string `json:"condition,omitempty"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// YieldPolicy is the Schema for the yieldpolicies API
// +kubebuilder:subresource:status
// +kubebuilder:resource:path=yieldpolicies,scope=Namespaced
type YieldPolicy struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec YieldPolicySpec `json:"spec,omitempty"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// YieldPolicyList contains a list of YieldPolicy
type YieldPolicyList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []YieldPolicy `json:"items"`
}

func init() {
	SchemeBuilder.Register(&YieldPolicy{}, &YieldPolicyList{})
}
