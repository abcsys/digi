package repo

import (
	"fmt"
	"testing"

	"digi.dev/digi/pkg/core"
)

func TestPull(t *testing.T) {
	name := "mock.digi.dev/v1/lamp"
	k, err := core.KindFromString(name)
	if err != nil {
		fmt.Printf("error parsing %s : %v", k, err)
	}
	if err := Pull(k); err != nil {
		fmt.Printf("error pulling %s : %v", k, err)
	}
}
