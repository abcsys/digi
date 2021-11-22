package query

import (
	"github.com/spf13/cobra"

	"digi.dev/digi/cmd/digi/helper"
)

var RootCmd = &cobra.Command{
	Use:   "query [command]",
	Short: "Query a digi",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		_ = Query(args[0])
	},
}

func Query(q string) error {
	return helper.RunMake(map[string]string{
		"QUERY": q,
	}, "query", false)
}