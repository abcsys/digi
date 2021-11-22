package lake

import (
	"github.com/spf13/cobra"

	"digi.dev/digi/cmd/digi/helper"
)

var (
	QueryCmd = &cobra.Command{
		Use:   "query [command]",
		Short: "Query the digi lake",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			_ = Query(args[0])
		},
	}

	ManageCmd = &cobra.Command{
		Use:   "lake [command]",
		Short: "Manage the digi lake",
		Args:  cobra.MinimumNArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			// TBD
		},
	}

	ConnectCmd = &cobra.Command{
		// TBD allow passing lake name
		Use:   "connect",
		Short: "Port forward to the digi lake",
		Run: func(cmd *cobra.Command, args []string) {
			_ = helper.RunMake(map[string]string{
			}, "port", false)
		},
	}
)

func Query(q string) error {
	return helper.RunMake(map[string]string{
		"QUERY": q,
	}, "query", false)
}

func init() {
	ManageCmd.AddCommand(ConnectCmd)
}
