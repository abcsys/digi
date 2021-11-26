package lake

import (
	"fmt"
	"strings"

	"digi.dev/digi/cmd/digi/helper"
	"github.com/spf13/cobra"
)

var (
	QueryCmd = &cobra.Command{
		Use:   "query [NAME] QUERY",
		Short: "Query a digi or the digi lake",
		Args:  cobra.MinimumNArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			var name, query string
			if len(args) > 1 {
				name, query = args[0], args[1]
			} else {
				if isQuery(args[0]) {
					name, query = "", args[0]
				} else {
					name, query = args[0], ""
				}
			}
			_ = Query(name, query)
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

func Query(name, query string) error {
	if name != "" {
		if query != "" {
			query = fmt.Sprintf("from %s | %s", name, query)
		} else {
			query = fmt.Sprintf("from %s", name)
		}
	}

	return helper.RunMake(map[string]string{
		"QUERY": query,
	}, "query", false)
}

func isQuery(s string) bool {
	return len(strings.Split(s, " ")) > 1
}

func init() {
	ManageCmd.AddCommand(ConnectCmd)
}
