package main

import (
	"fmt"
	"os"

	"digi.dev/digi/cmd/digi/lake"
	"github.com/spf13/cobra"
)

var RootCmd = &cobra.Command{
	Use:   "dq [OPTIONS] [NAME] QUERY",
	Short: lake.QueryCmd.Short,
	Args:  lake.QueryCmd.Args,
	Run:   lake.QueryCmd.Run,
}

// TBD add lake management commands

func main() {
	RootCmd.CompletionOptions.DisableDefaultCmd = true

	if err := RootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
