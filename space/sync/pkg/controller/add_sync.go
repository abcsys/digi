package controller

import (
	"digi.dev/digi/space/sync/pkg/controller/sync"
)

func init() {
	// AddToManagerFuncs is a list of functions to create controllers and add them to a manager.
	AddToManagerFuncs = append(AddToManagerFuncs, sync.Add)
}
