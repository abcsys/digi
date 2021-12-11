package main

import (
	"fmt"
	"os"

	"digi.dev/digi/api"
	"digi.dev/digi/cmd/digi/helper"
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
	Short: "Initialize a new digi kind",
	Long:  "Create a digi template with the directory name defaults to the kind",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")

		kind := args[0]
		params := map[string]string{
			"KIND": kind,
			// default configs
			"GROUP":     "digi.dev",
			"VERSION":   "v1",
			"IMAGE_DIR": kind,
		}

		if g, _ := cmd.Flags().GetString("group"); g != "" {
			params["GROUP"] = g
		}
		if v, _ := cmd.Flags().GetString("version"); v != "" {
			params["VERSION"] = v
		}
		if d, _ := cmd.Flags().GetString("directory"); d != "" {
			params["IMAGE_DIR"] = d
		}

		_ = helper.RunMake(params, "init", q)
		if !q {
			fmt.Println(kind)
		}
	},
}

var genCmd = &cobra.Command{
	Use:   "gen KIND",
	Short: "Generate configs and scripts",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")

		imageDir := args[0]
		if _ = helper.RunMake(map[string]string{
			"IMAGE_DIR": imageDir,
		}, "gen", q); !q {
			fmt.Println(imageDir)
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

		imageDir := args[0]
		kind, err := helper.GetKindFromImageDir(imageDir)
		if err != nil {
			panic(err)
		}

		if _ = helper.RunMake(map[string]string{
			"GROUP":     kind.Group,
			"VERSION":   kind.Version,
			"KIND":      kind.Name,
			"IMAGE_DIR": imageDir,
			"BUILDFLAG": buildFlag,
		}, "build", q); !q {
			fmt.Println(kind)
		}
	},
}

var imageCmd = &cobra.Command{
	Use:   "kind",
	Aliases: []string{"kinds", "image", "images"},
	Short: "List available kinds",
	Args:  cobra.ExactArgs(0),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")
		if !q {
			fmt.Println("KIND")
		}
		_ = helper.RunMake(nil, "image", q)
	},
}

// TBD pull and push to a remote repo
var pullCmd = &cobra.Command{
	Use:   "pull KIND",
	Short: "Pull an image",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")

		_ = helper.RunMake(map[string]string{
			"IMAGE_NAME": args[0],
		}, "pull", q)
	},
}

var pushCmd = &cobra.Command{
	Use:   "push KIND",
	Short: "Push an image",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")

		imageDir := args[0]
		kind, err := helper.GetKindFromImageDir(imageDir)
		if err != nil {
			panic(err)
		}

		if _ = helper.RunMake(map[string]string{
			"GROUP":     kind.Group,
			"VERSION":   kind.Version,
			"KIND":      kind.Name,
			"IMAGE_DIR": imageDir,
		}, "push", q); !q {
			fmt.Println(kind)
		}
	},
}

var testCmd = &cobra.Command{
	Use:   "test KIND",
	Short: "Test run a digi driver",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		var name, imageDir string

		imageDir = args[0]
		kind, err := helper.GetKindFromImageDir(imageDir)
		if err != nil {
			panic(err)
		}

		name = kind.Name + "-test"

		var useMounter string
		if um, _ := cmd.Flags().GetBool("mounter"); um {
			useMounter = "true"
		} else {
			useMounter = "false"
		}

		params := map[string]string{
			"IMAGE_DIR": imageDir,
			"GROUP":     kind.Group,
			"VERSION":   kind.Version,
			"KIND":      kind.Name,
			"PLURAL":    kind.Plural(),
			"NAME":      name,
			"NAMESPACE": "default",
			"MOUNTER":   useMounter,
		}

		if noAlias, _ := cmd.Flags().GetBool("no-alias"); !noAlias {
			// create alias beforehand because the test will hang
			if err := helper.CreateAlias(kind, name, "default"); err != nil {
				panic(err)
			}
			// TBD defer remove alias
		}

		var cmdStr string
		c, _ := cmd.Flags().GetBool("clean")
		if cmdStr = "test"; c {
			cmdStr = "clean-test"
		}

		_ = helper.RunMake(params, cmdStr, false)
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
		_ = helper.RunMake(map[string]string{
			"NAME": name,
		}, "log", q)
	},
}

var editCmd = &cobra.Command{
	Use:   "edit NAME",
	Short: "Edit a digi model",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		// TBD allow namespace
		var name string

		name = args[0]
		auri, err := api.Resolve(name)
		if err != nil {
			fmt.Printf("unknown digi kind from alias given name %s: %v\n", name, err)
			os.Exit(1)
		}

		_ = helper.RunMake(map[string]string{
			"GROUP":  auri.Kind.Group,
			"KIND":   auri.Kind.Name,
			"PLURAL": auri.Kind.Plural(),
			"NAME":   name,
		}, "edit", false)
	},
}

var runCmd = &cobra.Command{
	Use:   "run KIND NAME",
	Short: "Run a digi given kind and name",
	// TBD enable passing namespace
	Args: cobra.ExactArgs(2),
	Run: func(cmd *cobra.Command, args []string) {
		var imageDir, name = args[0], args[1]
		kind, err := helper.GetKindFromImageDir(imageDir)
		if err != nil {
			panic(err)
		}

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
		// XXX fix returned error and quiet from RunMake
		if err := helper.RunMake(map[string]string{
			"IMAGE_DIR": imageDir,
			"GROUP":     kind.Group,
			"VERSION":   kind.Version,
			"KIND":      kind.Name,
			"PLURAL":    kind.Plural(),
			"NAME":      name,
			"KOPFLOG":   kopfLog,
		}, c, quiet); err == nil {
			if !quiet {
				fmt.Println(name)
			}

			if !noAlias {
				err := helper.CreateAlias(kind, name, "default")
				if err != nil {
					fmt.Println("unable to create alias")
				}
			}
		}
	},
}

var stopCmd = &cobra.Command{
	Use:   "stop NAME",
	Short: "Stop a digi given the name",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")

		name := args[0]
		auri, err := api.Resolve(name)
		if err != nil {
			fmt.Printf("unknown digi kind from alias given name %s: %v\n", name, err)
			os.Exit(1)
		}

		kind := auri.Kind

		_ = helper.RunMake(map[string]string{
			"GROUP":   kind.Group,
			"VERSION": kind.Version,
			"KIND":    kind.Name,
			"PLURAL":  kind.Plural(),
			"NAME":    name,
		}, "stop", q)
	},
}

var rmkCmd = &cobra.Command{
	Use:   "rmk KIND",
	Short: "Remove a digi kind locally",
	Aliases: []string{"rmi"},
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")
		if _ = helper.RunMake(map[string]string{
			"IMAGE_DIR": args[0],
		}, "delete", q); !q {
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
		fmt.Println("NAME")
		_ = helper.RunMake(nil, "list", false)
	},
}

var watchCmd = &cobra.Command{
	Use:     "watch NAME",
	Short:   "Watch changes of a digi's model",
	Aliases: []string{"w"},
	Args:    cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		i, _ := cmd.Flags().GetFloat32("interval")
		v, _ := cmd.Flags().GetInt8("verbosity")

		name := args[0]
		auri, err := api.Resolve(name)
		if err != nil {
			fmt.Printf("unknown digi kind from alias given name %s: %v\n", name, err)
			os.Exit(1)
		}
		kind := auri.Kind

		params := map[string]string{
			"GROUP":    kind.Group,
			"VERSION":  kind.Version,
			"KIND":     kind.Name,
			"PLURAL":   kind.Plural(),
			"NAME":     name,
			"INTERVAL": fmt.Sprintf("%f", i),
			// TBD get max neat level from kubectl-neat
			"NEATLEVEL": fmt.Sprintf("-l %d", 4-v),
		}

		_ = helper.RunMake(params, "watch", false)
	},
}

var gcCmd = &cobra.Command{
	Use:     "gc",
	Short:   "Run garbage collection",
	Aliases: []string{"clean"},
	Args:    cobra.ExactArgs(0),
	Run: func(cmd *cobra.Command, args []string) {
		_ = helper.RunMake(map[string]string{}, "gc", false)
	},
}