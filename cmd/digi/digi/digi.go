package digi

import (
	"fmt"
	"log"
	"os"
	"strings"
	"sync"

	"digi.dev/digi/api"
	"digi.dev/digi/cmd/digi/helper"
	"digi.dev/digi/pkg/core"
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
	Use:     "init KIND",
	Short:   "Initialize a new kind",
	Long:    "Create a digi template with the directory name defaults to the kind",
	Aliases: []string{"i"},
	Args:    cobra.ExactArgs(1),
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

		_ = helper.RunMake(params, "init", true, q)
		if !q {
			fmt.Println(kind)
		}
	},
}

var genCmd = &cobra.Command{
	Use:     "gen KIND",
	Short:   "Generate configs for a kind",
	Aliases: []string{"g"},
	Args:    cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")

		imageDir := args[0]
		if _ = helper.RunMake(map[string]string{
			"IMAGE_DIR": imageDir,
		}, "gen", true, q); !q {
			fmt.Println(imageDir)
		}
	},
}

var buildCmd = &cobra.Command{
	Use:     "build KIND",
	Short:   "Build a kind",
	Aliases: []string{"b"},
	Args:    cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")
		noCache, _ := cmd.Flags().GetBool("no-cache")
		var buildFlag, pushFlag string
		if q {
			buildFlag += " -q"
			pushFlag += " -q"
		}
		if noCache {
			buildFlag += " --no-cache"
		}

		imageDir := args[0]
		kind, err := helper.GetKindFromImageDir(imageDir)
		if err != nil {
			log.Fatalf("unable to find kind %s\n", imageDir)
		}

		if _ = helper.RunMake(map[string]string{
			"GROUP":     kind.Group,
			"VERSION":   kind.Version,
			"KIND":      kind.Name,
			"IMAGE_DIR": imageDir,
			"BUILDFLAG": buildFlag,
			"PUSHFLAG":  pushFlag,
		}, "build", true, q); !q {
			fmt.Println(kind.Name)
		}
	},
}

var kindCmd = &cobra.Command{
	Use:     "kind",
	Short:   "List available kinds",
	Aliases: []string{"kinds", "image", "images", "k"},
	Args:    cobra.ExactArgs(0),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")
		if !q {
			fmt.Println("KIND")
		}
		_ = helper.RunMake(nil, "image", true, q)
	},
}

// TBD pull and push to a remote repo
var pullCmd = &cobra.Command{
	Use:   "pull KIND",
	Short: "Pull a kind",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")

		_ = helper.RunMake(map[string]string{
			"IMAGE_NAME": args[0],
		}, "pull", true, q)
	},
}

var pushCmd = &cobra.Command{
	Use:   "push KIND",
	Short: "Push a kind",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")

		imageDir := args[0]
		kind, err := helper.GetKindFromImageDir(imageDir)
		if err != nil {
			log.Fatalf("unable to find kind %s\n", imageDir)
		}

		if _ = helper.RunMake(map[string]string{
			"GROUP":     kind.Group,
			"VERSION":   kind.Version,
			"KIND":      kind.Name,
			"IMAGE_DIR": imageDir,
		}, "push", true, q); !q {
			fmt.Println(kind)
		}
	},
}

var testCmd = &cobra.Command{
	Use:     "test KIND",
	Short:   "Test run a digi's driver",
	Aliases: []string{"t"},
	Args:    cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		var name, imageDir string

		imageDir = args[0]
		kind, err := helper.GetKindFromImageDir(imageDir)
		if err != nil {
			log.Fatalf("unable to find kind %s\n", imageDir)
		}

		name = kind.Name + "-test"

		var useMounter, useStrictMounter string
		if um, _ := cmd.Flags().GetBool("mounter"); um {
			useMounter = "true"
		} else {
			useMounter = "false"
		}

		if um, _ := cmd.Flags().GetBool("strict-mounter"); um {
			useStrictMounter = "true"
		} else {
			useStrictMounter = "false"
		}

		params := map[string]string{
			"IMAGE_DIR":    imageDir,
			"GROUP":        kind.Group,
			"VERSION":      kind.Version,
			"KIND":         kind.Name,
			"PLURAL":       kind.Plural(),
			"NAME":         name,
			"NAMESPACE":    "default",
			"MOUNTER":      useMounter,
			"STRICT_MOUNT": useStrictMounter,
		}

		if noAlias, _ := cmd.Flags().GetBool("no-alias"); !noAlias {
			// create alias beforehand because the test will hang
			if err := helper.CreateAlias(kind, name, "default"); err != nil {
				log.Fatalf("unable to create alias: %v\n", err)
			}
			// TBD defer remove alias
		}

		var cmdStr string
		c, _ := cmd.Flags().GetBool("clean")
		if cmdStr = "test"; c {
			cmdStr = "clean-test"
		}

		_ = helper.RunMake(params, cmdStr, true, false)
	},
}

var logCmd = &cobra.Command{
	Use:     "log NAME",
	Short:   "Print log of a digi's driver",
	Aliases: []string{"logs", "l"},
	Args:    cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")

		name := args[0]
		_ = helper.RunMake(map[string]string{
			"NAME": name,
		}, "log", true, q)
	},
}

var editCmd = &cobra.Command{
	Use:     "edit NAME",
	Short:   "Edit a digi's model",
	Aliases: []string{"e"},
	Args:    cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		editAll, _ := cmd.Flags().GetBool("all")

		// TBD allow namespace
		var name string

		name = args[0]
		duri, err := api.Resolve(name)
		if err != nil {
			log.Fatalf("unable to resolve digi name %s: %v\n", name, err)
		}

		var cmdStr string
		if cmdStr = "edit"; editAll {
			cmdStr = "edit-all"
		}

		f, err := os.CreateTemp("", "digi-edit-"+name)
		if err != nil {
			log.Fatalln(err)
		}
		if err = f.Close(); err != nil {
			log.Fatalln(err)
		}
		path := f.Name()
		_ = helper.RunMake(map[string]string{
			"GROUP":  duri.Kind.Group,
			"KIND":   duri.Kind.Name,
			"PLURAL": duri.Kind.Plural(),
			"NAME":   name,
			"FILE":   path,
		}, cmdStr, true, false)
		_ = os.Remove(path)
	},
}

var runCmd = &cobra.Command{
	Use:   "run KIND NAME [NAME ...]",
	Short: "Run a digi given kind and name",
	Long: "Run a digi given kind and name; more than one name can be given. " +
		"The kind should be accessible in current path",
	Aliases: []string{"r"},
	// TBD enable passing namespace
	Args: cobra.MinimumNArgs(2),
	Run: func(cmd *cobra.Command, args []string) {
		var imageDir = args[0]
		kind, err := helper.GetKindFromImageDir(imageDir)
		if err != nil {
			log.Fatalf("unable to find kind %s\n", imageDir)
		}

		quiet, _ := cmd.Flags().GetBool("quiet")
		kopfLog := "false"
		if k, _ := cmd.Flags().GetBool("kopf-log"); k {
			kopfLog = "true"
		}
		noAlias, _ := cmd.Flags().GetBool("no-alias")
		debug, _ := cmd.Flags().GetBool("debug")
		var runFlag string
		if debug {
			runFlag += " --set trim_mount_on_load=false"
		}

		var names []string
		names = args[1:]

		var wg sync.WaitGroup
		logger := log.New(os.Stdout, "", 0)

		for _, name := range names {
			name = strings.TrimSpace(name)

			wg.Add(1)
			go func(name string, quiet bool) {
				defer wg.Done()
				if err := helper.RunMake(map[string]string{
					"IMAGE_DIR": imageDir,
					"GROUP":     kind.Group,
					"VERSION":   kind.Version,
					"KIND":      kind.Name,
					"PLURAL":    kind.Plural(),
					"NAME":      name,
					"KOPFLOG":   kopfLog,
					"RUNFLAG":   runFlag,
				}, "run", debug, quiet); err == nil {
					if !noAlias {
						err := helper.CreateAlias(kind, name, "default")
						if err != nil {
							logger.Println("unable to create alias")
						}
					}
				}
			}(name, quiet)
		}
		wg.Wait()
	},
}

var stopCmd = &cobra.Command{
	Use:     "stop NAME [NAME ...]",
	Short:   "Stop a digi given the name",
	Long:    "Stop a digi given the name",
	Aliases: []string{"s"},
	Args:    cobra.MinimumNArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		quiet, _ := cmd.Flags().GetBool("quiet")
		kindStr, _ := cmd.Flags().GetString("kind")

		// TBD handle namespace
		var kind *core.Kind
		if kindStr != "" {
			var err error
			if kind, err = core.KindFromString(kindStr); err != nil {
				log.Fatalf("unable to parse kind %s: %v\n", kindStr, err)
			}
		}

		var wg sync.WaitGroup

		for _, name := range args {
			name = strings.TrimSpace(name)
			if kindStr == "" {
				duri, err := api.Resolve(name)
				if err != nil {
					log.Fatalf("unknown digi kind from alias given name %s\n", name)
				}
				kind = &duri.Kind
			}

			wg.Add(1)
			go func(name string, quiet bool) {
				defer wg.Done()
				_ = helper.RunMake(map[string]string{
					"GROUP":   kind.Group,
					"VERSION": kind.Version,
					"KIND":    kind.Name,
					"PLURAL":  kind.Plural(),
					"NAME":    name,
				}, "stop", false, quiet)
			}(name, quiet)
		}
		wg.Wait()
	},
}

var rmkCmd = &cobra.Command{
	Use:     "rmk KIND",
	Short:   "Remove a kind locally",
	Aliases: []string{"rmi"},
	Args:    cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")
		if _ = helper.RunMake(map[string]string{
			"IMAGE_DIR": args[0],
		}, "delete", true, q); !q {
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
					log.Fatalln(err)
				}
				return
			}

			if len(args) == 1 {
				log.Fatalln("args should be either none or 2")
			}

			// parse the duri
			duri, err := api.ParseAuri(args[0])
			if err != nil {
				log.Fatalf("unable to parse duri %s: %v\n", args[0], err)
			}

			a := &api.Alias{
				Auri: &duri,
				Name: args[1],
			}

			if err := a.Set(); err != nil {
				log.Fatalln("unable to set alias: ", err)
			}
		},
	}
	aliasClearCmd = &cobra.Command{
		Use:   "clear",
		Short: "Clear all aliases",
		Args:  cobra.ExactArgs(0),
		Run: func(cmd *cobra.Command, args []string) {
			if err := api.ClearAlias(); err != nil {
				log.Fatalln("unable to clear alias: ", err)
			}
		},
	}
	aliasResolveCmd = &cobra.Command{
		Use:   "resolve ALIAS",
		Short: "Resolve an alias",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			if err := api.ResolveFromLocal(args[0]); err != nil {
				log.Fatalf("unable to resolve alias %s: %v\n", args[0], err)
			}
		},
	}
)

var listCmd = &cobra.Command{
	Use:     "list",
	Short:   "Get a list of running digis",
	Aliases: []string{"ps", "ls"},
	Args:    cobra.ExactArgs(0),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")
		showAll, _ := cmd.Flags().GetBool("all")
		if !q {
			fmt.Println("NAME")
		}
		flags := ""
		if !showAll {
			flags += " -l app!=lake"
		}
		_ = helper.RunMake(map[string]string{
			"FLAG": flags,
		}, "list", true, false)
	},
}

var checkCmd = &cobra.Command{
	Use:     "check NAME",
	Short:   "Print a digi's model",
	Aliases: []string{"c"},
	Args:    cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		v, _ := cmd.Flags().GetInt8("verbosity")

		name := args[0]
		duri, err := api.Resolve(name)
		if err != nil {
			log.Fatalf("unknown digi kind from alias given name %s: %v\n", name, err)
		}
		kind := duri.Kind

		params := map[string]string{
			"GROUP":    kind.Group,
			"VERSION":  kind.Version,
			"KIND":     kind.Name,
			"PLURAL":   kind.Plural(),
			"NAME":     name,
			// TBD get max neat level from kubectl-neat
			"NEATLEVEL": fmt.Sprintf("-l %d", 4-v),
		}

		_ = helper.RunMake(params, "check", true, false)
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
		duri, err := api.Resolve(name)
		if err != nil {
			log.Fatalf("unknown digi kind from alias given name %s: %v\n", name, err)
		}
		kind := duri.Kind

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

		_ = helper.RunMake(params, "watch", true, false)
	},
}

var gcCmd = &cobra.Command{
	Use:     "gc",
	Short:   "Run garbage collection",
	Aliases: []string{"clean"},
	Args:    cobra.ExactArgs(0),
	Run: func(cmd *cobra.Command, args []string) {
		_ = helper.RunMake(map[string]string{}, "gc", true, false)
	},
}
