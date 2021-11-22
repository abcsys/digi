package main

import (
	"fmt"
	"os"

	"digi.dev/digi/cmd/digi/query"
	"github.com/spf13/cobra"
)

var RootCmd = &cobra.Command{
	Use:   "dq [options] QUERY",
	Short: "Query a digi",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		_ = query.Query(args[0])
	},
}

func main(){
	RootCmd.CompletionOptions.DisableDefaultCmd = true

	if err := RootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}

