package space

import (
	"fmt"
	"log"

	"digi.dev/digi/api"
	"digi.dev/digi/cmd/digi/helper"
	"digi.dev/digi/space"
	"github.com/spf13/cobra"
)

var (
	controllers = map[string]bool{
		"lake":    true,
		"syncer":  true,
		"mounter": true,
		// ...
	}
)

var RootCmd = &cobra.Command{
	Use:   "space [command]",
	Short: "Manage digis in a dSpace",
}

var mountCmd = &cobra.Command{
	Use:     "mount SRC [SRC..] TARGET",
	Short:   "Mount a digi to another",
	Aliases: []string{"m"},
	Args:    cobra.MinimumNArgs(2),
	Run: func(cmd *cobra.Command, args []string) {
		mode, _ := cmd.Flags().GetString("mode")
		sources := args[:len(args)-1]
		target := args[len(args)-1]

		op := api.MOUNT
		if d, _ := cmd.Flags().GetBool("yield"); d {
			op = api.YIELD
		}
		if d, _ := cmd.Flags().GetBool("activate"); d {
			op = api.ACTIVATE
		}
		if d, _ := cmd.Flags().GetBool("delete"); d {
			op = api.UNMOUNT
		}

		mt, err := api.NewMounter(sources, target, op, mode)
		if err != nil {
			log.Fatalln(err)
		}

		if err = mt.Do(); err != nil {
			log.Fatalf("failed: %v\n", err)
		}
	},
}

var pipeCmd = &cobra.Command{
	Use:     "pipe [SRC TARGET] [\"d1 | d2 | ..\"]",
	Short:   "Pipe a digi's input to another's output",
	Aliases: []string{"p"},
	Args:    cobra.MinimumNArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		var pp *api.Piper
		var err error

		if len(args) == 1 {
			pp, err = api.NewChainPiperFromStr(args[0])
		} else {
			pp, err = api.NewPiper(args[0], args[1])
		}

		if err != nil {
			log.Fatalln(err)
		}

		f := pp.Pipe
		if d, _ := cmd.Flags().GetBool("delete"); d {
			f = pp.Unpipe
		}
		if err = f(); err != nil {
			log.Fatalf("pipe failed: %v\n", err)
		}
	},
}

var startCmd = &cobra.Command{
	Use:     "start [NAME ...]",
	Short:   "Start space controllers",
	Aliases: []string{"init"},
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) == 0 {
			_ = helper.RunMake(nil, "start-space", true, false)
		} else {
			for _, name := range args {
				if ok, _ := controllers[name]; !ok {
					log.Fatalf("unknown controller: %s\n", name)
				}
				_ = helper.RunMake(nil, "start-"+name, true, false)
			}
		}
	},
}

var stopCmd = &cobra.Command{
	Use:   "stop [NAME ...]",
	Short: "Stop space controllers",
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) == 0 {
			_ = helper.RunMake(nil, "stop-space", true, false)
		} else {
			for _, name := range args {
				if ok, _ := controllers[name]; !ok {
					log.Fatalf("unknown controller: %s\n", name)
				}
				_ = helper.RunMake(nil, "stop-"+name, true, false)
			}
		}
	},
}

var listCmd = &cobra.Command{
	Use:     "list",
	Short:   "List available digi spaces",
	Aliases: []string{"ls", "l"},
	Args:    cobra.ExactArgs(0),
	Run: func(cmd *cobra.Command, args []string) {
		var flags string
		q, _ := cmd.Flags().GetBool("quiet")
		c, _ := cmd.Flags().GetBool("current")
		if c {
			flags += " -c"
		}
		if !q {
			fmt.Println("NAME")
		}
		_ = helper.RunMake(map[string]string{
			"FLAG": flags,
		}, "list-space", true, false)

	},
}

var checkCmd = &cobra.Command{
	Use:     "check",
	Short:   "Print space info",
	Aliases: []string{"show", "ch"},
	Args:    cobra.MaximumNArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		params := make(map[string]string)
		if len(args) == 1 {
			params["SPACE"] = args[0]
		}
		_ = helper.RunMake(params, "show-space", true, false)
	},
}

var switchCmd = &cobra.Command{
	Use:     "checkout NAME",
	Short:   "Switch to a digi space",
	Aliases: []string{"checkout", "c", "switch"},
	Args:    cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		// TBD switch should take care of local alias cache, e.g., per
		// space configuration file; v0.2 should probably support exporting
		// aliases from a space to allow access digis created else where
		_ = helper.RunMake(map[string]string{
			"NAME": args[0],
		}, "switch-space", true, false)
	},
}

var aliasCmd = &cobra.Command{
	Use:     "alias OLD_NAME NAME",
	Short:   "Update the local alias to a space",
	Aliases: []string{"rename"},
	Args:    cobra.ExactArgs(2),
	Run: func(cmd *cobra.Command, args []string) {
		// TBD alias in a space should have its own section in the
		//	config file ('digictx'); upon checkout, both the kubectx
		//	and digictx should get switched
		_ = helper.RunMake(map[string]string{
			"OLD_NAME": args[0],
			"NAME":     args[1],
		}, "rename-space", true, false)
	},
}

var connectCmd = &cobra.Command{
	Use:     "connect NAME",
	Short:   "Start a tty on the digi's driver",
	Aliases: []string{"conn", "c"},
	Args:    cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		useBash, _ := cmd.Flags().GetBool("bash")
		params := map[string]string{
			"NAME": args[0],
		}
		if useBash {
			params["SHELL_BIN"] = "bash"
		}
		_ = helper.RunMake(params, "connect", true, false)
	},
}

func init() {
	log.SetFlags(0)
	// TBD delete digi space removes all running digis and controllers
	RootCmd.AddCommand(startCmd)
	RootCmd.AddCommand(stopCmd)

	RootCmd.AddCommand(mountCmd)
	mountCmd.Flags().BoolP("delete", "d", false, "Unmount source from target")
	mountCmd.Flags().BoolP("yield", "y", false, "Yield a mount")
	mountCmd.Flags().BoolP("activate", "a", false, "Activate a mount")
	mountCmd.Flags().StringP("mode", "m", space.DefaultMountMode, "Set mount mode")

	RootCmd.AddCommand(pipeCmd)
	pipeCmd.Flags().BoolP("delete", "d", false, "Unpipe source from target")

	RootCmd.AddCommand(listCmd)
	RootCmd.AddCommand(checkCmd)
	RootCmd.AddCommand(switchCmd)
	RootCmd.AddCommand(aliasCmd)
	// TBD promote connect to digi root
	RootCmd.AddCommand(connectCmd)
	listCmd.Flags().BoolP("current", "c", false, "List current space")
	connectCmd.Flags().BoolP("bash", "b", false, "Use bash in remote session")
}
