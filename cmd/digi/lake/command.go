package lake

import (
	"fmt"
	"log"
	"strings"

	"digi.dev/digi/cmd/digi/helper"
	"github.com/spf13/cobra"
	"github.com/spf13/pflag"
)

var (
	QueryCmd = &cobra.Command{
		Use:     "query [OPTIONS] [NAME] QUERY",
		Short:   "Query a digi or the digi lake",
		Aliases: []string{"q"},
		Args:    cobra.MinimumNArgs(1),
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
			_ = Query(name, query, cmd.Flags())
		},
	}

	RootCmd = &cobra.Command{
		Use:   "lake [command]",
		Short: "Manage the digi lake",
		Args:  cobra.MinimumNArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			// TBD
		},
	}

	startCmd = &cobra.Command{
		Use:     "start [command]",
		Short:   "Start the digi lake",
		Aliases: []string{"init"},
		Args:    cobra.MinimumNArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			// TBD
		},
	}

	connectCmd = &cobra.Command{
		// TBD allow passing lake name
		Use:   "connect",
		Short: "Port forward to the digi lake",
		Run: func(cmd *cobra.Command, args []string) {
			_ = helper.RunMake(map[string]string{}, "connect-lake", true, false)
		},
	}
)

func isQuery(s string) bool {
	return len(strings.Split(s, " ")) > 1
}

func Query(name, query string, flags *pflag.FlagSet) error {
	if name != "" {
		if query != "" {
			query = fmt.Sprintf("from '%s' | %s", name, query)
		} else {
			query = fmt.Sprintf("from '%s'", name)
		}
	}

	var flagStr string
	for _, f := range []struct {
		short string
		full  string
	}{
		{"f", "format"},
		{"Z", ""},
		// ...
	} {
		switch f.full {
		case "":
			b, _ := flags.GetBool(f.short)
			if b {
				flagStr += fmt.Sprintf("-%s  ", f.short)
			}
			break
		default:
			s, _ := flags.GetString(f.full)
			if s != "" {
				flagStr += fmt.Sprintf("-%s %s ", f.short, s)
			}
		}
	}

	return helper.RunMake(map[string]string{
		"QUERY": query,
		"FLAG":  flagStr,
	}, "query", true, false)
}

func init() {
	// TBD read from cmdline flag
	log.SetFlags(0)

	RootCmd.AddCommand(connectCmd)
	RootCmd.AddCommand(startCmd)

	QueryCmd.Flags().StringP("format", "f", "", "Output data format.")
	QueryCmd.Flags().BoolP("Z", "Z", false, "Pretty formatted output.")
	// ...
}
