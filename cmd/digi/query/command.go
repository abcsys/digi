package query

import "github.com/spf13/cobra"

var RootCmd = &cobra.Command{
	Use:   "query [command]",
	Short: "Query a digi",
}