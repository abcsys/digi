package main

import (
	"fmt"
	"os"

	"digi.dev/digi/cmd/digi/lake"
	"github.com/spf13/cobra"
)

var RootCmd = &cobra.Command{
	Use:   "dq [options] QUERY",
	Short: "Query a digi",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		_ = lake.Query(args[0])
	},
}

// TBD add lake management commands

func main(){
	RootCmd.CompletionOptions.DisableDefaultCmd = true

	if err := RootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}

