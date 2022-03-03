package sidecar

import (
	"github.com/spf13/cobra"

	"digi.dev/digi/cmd/digi/helper"
)

var (
	RootCmd = &cobra.Command{
		Use:   "sidecar [command]",
		Short: "Create and manage sidecars",
		Aliases: []string{"sc"},
		Args:  cobra.MinimumNArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
		},
	}

	viewCmd = &cobra.Command{
		Use:   "view NAME",
		Short: "Create a materialized view on a digi",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			var cmdStr string
			var params map[string]string
			params = map[string]string{
				"NAME": args[0],
			}
			cmdStr = "view"
			_ = helper.RunMake(params, cmdStr, true, false)
		},
	}
)

func init() {
	RootCmd.AddCommand(viewCmd)
}
