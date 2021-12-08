package main

import (
	"fmt"
	"os"
	"strings"

	"digi.dev/digi/api"
	"digi.dev/digi/cmd/digi/helper"
	"github.com/jinzhu/inflection"
	"github.com/spf13/cobra"
)

var (
	RootCmd = &cobra.Command{
		Use:   "digi <command> [options] [arguments...]",
		Short: "command line digi manager",
		Long: `
    Command-line digi manager.
    `,
	}
)

var initCmd = &cobra.Command{
	Use:   "init KIND",
	Short: "Initialize a digi template",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")

		kind := args[0]
		params := map[string]string{
			"KIND": kind,
		}
		if g, _ := cmd.Flags().GetString("group"); g != "" {
			params["GROUP"] = g
		}
		if v, _ := cmd.Flags().GetString("version"); v != "" {
			params["VERSION"] = v
		}
		if err := helper.RunMake(params, "init", q); err == nil && !q {
			fmt.Println(kind)
		}
	},
}

var genCmd = &cobra.Command{
	Use:   "gen KIND",
	Short: "Generate configs and scripts in an image",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")

		kind := args[0]
		if err := helper.RunMake(map[string]string{
			"KIND": kind,
		}, "gen", q); err == nil && !q {
			fmt.Println(kind)
		}
	},
}

var buildCmd = &cobra.Command{
	Use:   "build KIND",
	Short: "Build a digi image",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")
		var buildFlag string
		if q {
			buildFlag += "-q"
		}
		kind := args[0]
		if err := helper.RunMake(map[string]string{
			"KIND":      kind,
			"BUILDFLAG": buildFlag,
		}, "build", q); err == nil && !q {
			fmt.Println(kind)
		}
	},
}

var imageCmd = &cobra.Command{
	Use:   "image",
	Short: "List available digi images",
	Args:  cobra.ExactArgs(0),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")
		if !q {
			fmt.Println("IMAGE ID")
		}
		_ = helper.RunMake(nil, "image", q)
	},
}

// TBD pull and push to a remote repo
var pullCmd = &cobra.Command{
	Use:   "pull KIND",
	Short: "Pull a digi image",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")

		kind := args[0]
		if err := helper.RunMake(map[string]string{
			"KIND": kind,
		}, "pull", q); err != nil {
			return
		}

		if err := helper.RunMake(map[string]string{
			"KIND": kind,
		}, "build", true); err == nil && !q {
			fmt.Println(kind)
		}
	},
}

var pushCmd = &cobra.Command{
	Use:   "push KIND",
	Short: "Push a digi image",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")

		kind := args[0]
		if err := helper.RunMake(map[string]string{
			"KIND": kind,
		}, "push", q); err == nil && !q {
			fmt.Println(kind)
		}
	},
}

var testCmd = &cobra.Command{
	Use:   "test KIND",
	Short: "Test run a digi driver",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		c, _ := cmd.Flags().GetBool("clean")
		var cmdStr string
		if cmdStr = "test"; c {
			cmdStr = "clean-test"
		}

		noAlias, _ := cmd.Flags().GetBool("no-alias")
		params := map[string]string{
			"KIND":   args[0],
			"PLURAL": inflection.Plural(strings.ToLower(args[0])),
		}

		if !noAlias {
			// create alias beforehand because the test will hang
			helper.CreateAlias(args[0], args[0]+"-test", "default")
			// TBD defer remove alias
		}

		if err := helper.RunMake(params, cmdStr, false); err != nil {
		}
	},
}

var logCmd = &cobra.Command{
	Use:     "log NAME",
	Short:   "Print log of a digi driver",
	Aliases: []string{"logs"},
	Args:    cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")

		name := args[0]
		if err := helper.RunMake(map[string]string{
			"NAME": name,
		}, "log", q); err == nil && !q {
		}
	},
}

var editCmd = &cobra.Command{
	Use:   "edit [KIND] NAME",
	Short: "Edit a digi model",
	Args:  cobra.MinimumNArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		var name, kind string

		if len(args) == 1 {
			name = args[0]
			auri, err := api.Resolve(name)
			if err != nil {
				fmt.Printf("unknown digi kind from alias given name %s: %v\n", name, err)
				os.Exit(1)
			}
			kind = auri.Kind.Plural()
		} else {
			kind, name = args[0], args[1]
		}

		_ = helper.RunMake(map[string]string{
			"KIND": kind,
			"NAME": name,
		}, "edit", false)
	},
}

var runCmd = &cobra.Command{
	Use:   "run KIND NAME",
	Short: "Run a digi given kind and name",
	// TBD enable passing namespace
	Args: cobra.ExactArgs(2),
	Run: func(cmd *cobra.Command, args []string) {
		var c string
		if l, _ := cmd.Flags().GetBool("local"); l {
			c = "test"
		} else {
			c = "run"
		}

		kopfLog := "false"
		if k, _ := cmd.Flags().GetBool("kopf-log"); k {
			kopfLog = "true"
		}

		noAlias, _ := cmd.Flags().GetBool("no-alias")

		quiet, _ := cmd.Flags().GetBool("quiet")
		kind, name := args[0], args[1]
		if err := helper.RunMake(map[string]string{
			"KIND":    kind,
			"NAME":    name,
			"KOPFLOG": kopfLog,
		}, c, quiet); err == nil && !quiet {
			fmt.Println(name)

			if !noAlias {
				helper.CreateAlias(kind, name, "default")
			}
		}
	},
}

var stopCmd = &cobra.Command{
	Use:   "stop [KIND] NAME",
	Short: "Stop a digi given kind and name",
	Args:  cobra.MinimumNArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")

		var name, kind string

		if len(args) == 1 {
			name = args[0]
			auri, err := api.Resolve(name)
			if err != nil {
				fmt.Printf("unknown digi kind from alias given name %s: %v\n", name, err)
				os.Exit(1)
			}
			kind = auri.Kind.Plural()
		} else {
			kind, name = args[0], args[1]
		}

		if err := helper.RunMake(map[string]string{
			"KIND": kind,
			"NAME": name,
		}, "stop", q); err == nil && !q {
			fmt.Println(name)
		}
	},
}

var rmiCmd = &cobra.Command{
	Use:   "rmi KIND",
	Short: "Remove a digi image",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")
		if err := helper.RunMake(map[string]string{
			"KIND": args[0],
		}, "delete", q); err == nil && !q {
			fmt.Printf("%s removed\n", args[0])
		}
	},
}

var (
	aliasCmd = &cobra.Command{
		Use:   "alias [AURI ALIAS]",
		Short: "Create a digi alias",
		Args:  cobra.MaximumNArgs(2),
		Run: func(cmd *cobra.Command, args []string) {
			if len(args) == 0 {
				if err := api.ShowAll(); err != nil {
					fmt.Println(err)
					os.Exit(1)
				}
				os.Exit(0)
			}

			if len(args) == 1 {
				fmt.Println("args should be either none or 2")
				os.Exit(1)
			}

			// parse the auri
			auri, err := api.ParseAuri(args[0])
			if err != nil {
				fmt.Printf("unable to parse auri %s: %v\n", args[0], err)
				os.Exit(1)
			}

			a := &api.Alias{
				Auri: &auri,
				Name: args[1],
			}

			if err := a.Set(); err != nil {
				fmt.Println("unable to set alias: ", err)
				os.Exit(1)
			}
		},
	}
	aliasClearCmd = &cobra.Command{
		Use:   "clear",
		Short: "Clear all aliases",
		Args:  cobra.ExactArgs(0),
		Run: func(cmd *cobra.Command, args []string) {
			if err := api.ClearAlias(); err != nil {
				fmt.Println("unable to clear alias: ", err)
				os.Exit(1)
			}
		},
	}
	aliasResolveCmd = &cobra.Command{
		Use:   "resolve ALIAS",
		Short: "Resolve an alias",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			if err := api.ResolveFromLocal(args[0]); err != nil {
				fmt.Printf("unable to resolve alias %s: %v\n", args[0], err)
				os.Exit(1)
			}
		},
	}
)

var listCmd = &cobra.Command{
	Use:     "list",
	Short:   "Get a list of running digis",
	Aliases: []string{"ps"},
	Args:    cobra.ExactArgs(0),
	Run: func(cmd *cobra.Command, args []string) {
		_ = helper.RunMake(nil, "list", false)
	},
}

var watchCmd = &cobra.Command{
	Use:     "watch [KIND] NAME",
	Short:   "Watch changes of a digi's model",
	Aliases: []string{"w"},
	Args:    cobra.MinimumNArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		i, _ := cmd.Flags().GetFloat32("interval")
		l, _ := cmd.Flags().GetInt8("neat-level")

		var name, kind string

		if len(args) == 1 {
			name = args[0]
			auri, err := api.Resolve(name)
			if err != nil {
				fmt.Printf("unknown digi kind from alias given name %s: %v\n", name, err)
				os.Exit(1)
			}
			kind = auri.Kind.Plural()
		} else {
			kind, name = args[0], args[1]
		}

		params := map[string]string{
			"NAME":      name,
			"KIND":      kind,
			"INTERVAL":  fmt.Sprintf("%f", i),
			"NEATLEVEL": fmt.Sprintf("-l %d", l),
		}

		_ = helper.RunMake(params, "watch", false)
	},
}
