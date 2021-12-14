package main

import (
	"fmt"
	"os"

	"digi.dev/digi/cmd/digi/lake"
)

var RootCmd = lake.QueryCmd

func main() {
	RootCmd.CompletionOptions.DisableDefaultCmd = true
	RootCmd.Use = "dq [OPTIONS] [NAME] QUERY"

	if err := RootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
