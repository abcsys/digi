package space

import (
	"fmt"
	"os"

	"digi.dev/digi/api"
	"digi.dev/digi/space"
	"github.com/spf13/cobra"
)

var RootCmd = &cobra.Command{
	Use:   "space [command]",
	Short: "Manage digis in a dSpace",
}

var mountCmd = &cobra.Command{
	Use:   "mount SRC TARGET [ mode ]",
	Short: "Mount a digivice to another digivice",
	Args:  cobra.MinimumNArgs(2),
	Run: func(cmd *cobra.Command, args []string) {
		var mode string
		if len(args) < 3 {
			mode = space.DefaultMountMode
		} else {
			mode = args[2]
		}

		mt, err := api.NewMounter(args[0], args[1], mode)
		if err != nil {
			fmt.Println(err)
			os.Exit(1)
		}

		//fmt.Printf("mount %s -> %s\n", mt.Source.Name, mt.Target.Name)

		mt.Op = api.MOUNT

		if d, _ := cmd.Flags().GetBool("yield"); d {
			mt.Op = api.YIELD
		}

		if d, _ := cmd.Flags().GetBool("activate"); d {
			mt.Op = api.ACTIVATE
		}

		if d, _ := cmd.Flags().GetBool("delete"); d {
			mt.Op = api.UNMOUNT
		}

		if err = mt.Do(); err != nil {
			fmt.Printf("failed: %v\n", err)
			os.Exit(1)
		}
	},
}

var pipeCmd = &cobra.Command{
	Use:   "pipe [SRC TARGET] [\"d1 | d2 | ..\"]",
	Short: "Pipe a digidata's input.x to another's output.y",
	Args:  cobra.MinimumNArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		var pp *api.Piper
		var err error

		if len(args) == 1 {
			pp, err = api.NewChainPiperFromStr(args[0])
		} else {
			pp, err = api.NewPiper(args[0], args[1])
		}

		if err != nil {
			fmt.Println(err)
			os.Exit(1)
		}

		//fmt.Printf("pipe %s -> %s\n", pp.Source.Name, pp.Target.Name)

		f := pp.Pipe
		if d, _ := cmd.Flags().GetBool("delete"); d {
			f = pp.Unpipe
		}
		if err = f(); err != nil {
			fmt.Printf("pipe failed: %v\n", err)
			os.Exit(1)
		}
	},
}

func init() {
	RootCmd.AddCommand(mountCmd)
	mountCmd.Flags().BoolP("delete", "d", false, "Unmount source from target")
	mountCmd.Flags().BoolP("yield", "y", false, "Yield a mount")
	mountCmd.Flags().BoolP("activate", "a", false, "Activate a mount")

	RootCmd.AddCommand(pipeCmd)
	pipeCmd.Flags().BoolP("delete", "d", false, "Unpipe source from target")
}
