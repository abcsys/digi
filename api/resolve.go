package api

//import "k8s.io/apimachinery/pkg/types"
//
//// Given a namespace/name, return the Auri by querying the apiserver.
//// Use alias as an alternative.

// Resolve from local alias cache
func ResolveFromLocal(name string) error {
	return ResolveAndPrint(name)
}
