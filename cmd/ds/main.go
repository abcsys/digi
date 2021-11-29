package main

import (
	"fmt"
	"os"

	"digi.dev/digi/cmd/digi/space"
)

var RootCmd = space.RootCmd

func main() {
	RootCmd.CompletionOptions.DisableDefaultCmd = true
	RootCmd.Use = "ds [options] [arguments...]"

	if err := RootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
