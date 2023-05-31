package lake

import (
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"net/url"
	"strings"

	"github.com/spf13/cobra"
	"github.com/spf13/pflag"

	"digi.dev/digi/api/config"
	"digi.dev/digi/cmd/digi/helper"
	"digi.dev/digi/cmd/digi/space"
)

var (
	QueryCmd = &cobra.Command{
		Use:     "query [OPTIONS] [NAME(local)] USER_NAME/DSPACE/DIGI(remote) [QUERY] [EGRESS(remote)] [SOURCER_ADDRESS(remote)]",
		Short:   "Query a digi or the digi lake",
		Aliases: []string{"q"},
		Args:    cobra.MinimumNArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			if r, _ := cmd.Flags().GetBool("remote"); r {
				// query remotely through anysource
				digi_path := args[0]
				query := ""
				if len(args) > 1 {
					query = args[1]
				}
				egress := ""
				if len(args) > 2 {
					egress = args[2]
				}
				anysource := ""
				if len(args) > 3 {
					anysource = args[3]
				} else {
					config_ret, err := config.Get("ANYSOURCE_ADDRESS")
					if err != nil {
						log.Fatal("Provide a sourcer address or set an anysource address in the digi config\n")
					}
					anysource = config_ret
				}

				baseURL := fmt.Sprintf("http://%s:30202/sourcer/%s/query", anysource, digi_path)
				u, _ := url.ParseRequestURI(baseURL)
				params := url.Values{}
				if egress != "" {
					params.Add("egress", egress)
				}
				if query != "" {
					params.Add("query", query)
				}
				u.RawQuery = params.Encode()
				uStr := fmt.Sprintf("%v", u)
				resp, err := http.Get(uStr)
				if err != nil {
					log.Fatal("Failed to access sourcer at address: \n", uStr, "\n", err.Error())
				}

				defer resp.Body.Close()
				body, err := ioutil.ReadAll(resp.Body)
				if err != nil {
					log.Fatal("Failed to read response from sourcer: \n", body)
				}
				if resp.StatusCode != 200 {
					log.Fatal("Request to sourcer failed with code", resp.StatusCode, "\n", string(body))
				}

				// print query results to stdout
				fmt.Println(string(body))
			} else {
				// query local dspace through Zed lake
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
			}
		},
	}

	RootCmd = &cobra.Command{
		Use:   "lake [command]",
		Short: "Manage the digi lake",
		Args:  cobra.MinimumNArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
		},
	}

	startCmd = &cobra.Command{
		Use:     "start",
		Short:   "Start the digi lake",
		Aliases: []string{"start"},
		Args:    cobra.ExactArgs(0),
		Run: func(cmd *cobra.Command, args []string) {
			if err := space.StartController("lake"); err != nil {
				log.Fatalln(err)
			}
		},
	}

	stopCmd = &cobra.Command{
		Use:     "stop",
		Short:   "Stop the digi lake",
		Aliases: []string{"stop"},
		Args:    cobra.ExactArgs(0),
		Run: func(cmd *cobra.Command, args []string) {
			if err := space.StopController("lake"); err != nil {
				log.Fatalln(err)
			}
		},
	}

	connectCmd = &cobra.Command{
		// TBD allow passing lake name
		Use:   "connect",
		Short: "Port forward to the digi lake",
		Run: func(cmd *cobra.Command, args []string) {
			_ = helper.RunMake(map[string]string{}, "conn-lake", true, false)
		},
	}

	loadCmd = &cobra.Command{
		Use:   "load NAME FILE",
		Short: "load dataset to the pool",
		Args:  cobra.ExactArgs(2),
		Run: func(cmd *cobra.Command, args []string) {
			name, path := args[0], args[1]
			_ = helper.RunMake(map[string]string{
				"NAME": name,
				"FILE": path,
			}, "load", true, false)
		},
	}
)

func isQuery(s string) bool {
	return len(strings.Split(s, " ")) > 1
}

func Query(name, query string, flags *pflag.FlagSet) error {
	// TBD load filter meta somewhere centralized
	inFlow := "not __meta"
	// XXX makefile has bash -c "" with quotes, need to escape query
	query = strings.ReplaceAll(query, "\"", "\\\"")
	if name != "" {
		// TBD handle name as 'pool'@branch
		if query != "" {
			query = fmt.Sprintf("from %s | %s | %s", name, inFlow, query)
		} else {
			query = fmt.Sprintf("from %s | %s", name, inFlow)
		}
	} else if query != "" {
		// TBD insert inFlow after from in query
		query = fmt.Sprintf("%s | %s", query, inFlow)
	} else {
		return fmt.Errorf("missing query")
	}

	var flagStr string
	for _, f := range []struct {
		short string
		full  string
	}{
		{"f", "format"},
		{"Z", ""},
		// ...supported zed flags
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

	var cmdFlagStr string
	s, _ := flags.GetBool("timed")
	if s {
		cmdFlagStr += "TIMEFORMAT='%R s'; time"
	}

	return helper.RunMake(map[string]string{
		"QUERY":   query,
		"ZEDFLAG": flagStr,
		"FLAG":    cmdFlagStr,
	}, "query", true, false)
}

func init() {
	// TBD read from cmdline flag
	log.SetFlags(0)

	RootCmd.AddCommand(connectCmd)
	RootCmd.AddCommand(startCmd)
	RootCmd.AddCommand(stopCmd)
	RootCmd.AddCommand(loadCmd)

	QueryCmd.Flags().StringP("format", "f", "", "Output data format.")
	QueryCmd.Flags().BoolP("Z", "Z", false, "Pretty formatted output.")
	QueryCmd.Flags().BoolP("timed", "t", false, "Report the query latency.")
	// ...
}
