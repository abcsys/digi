package main

import (
	"fmt"
	"os"

	"digi.dev/digi/cmd/digi/box"
	"digi.dev/digi/cmd/digi/digi"
)

var RootCmd = digi.RootCmd

func init() {
	RootCmd.AddCommand(box.AttachCmd)
	RootCmd.AddCommand(box.ReplayCmd)
}

func main() {
	RootCmd.CompletionOptions.DisableDefaultCmd = true
	RootCmd.Use = "dbox [command]"

	if err := RootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
