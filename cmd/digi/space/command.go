package space

import (
	"digi.dev/digi/api"
	"digi.dev/digi/space"
	"github.com/spf13/cobra"
	"log"
)

var RootCmd = &cobra.Command{
	Use:   "space [command]",
	Short: "Manage digis in a dSpace",
}

var mountCmd = &cobra.Command{
	Use:     "mount SRC TARGET [ mode ]",
	Short:   "Mount a digi to another",
	Aliases: []string{"m"},
	Args:    cobra.MinimumNArgs(2),
	Run: func(cmd *cobra.Command, args []string) {
		var mode string
		if len(args) < 3 {
			mode = space.DefaultMountMode
		} else {
			mode = args[2]
		}

		mt, err := api.NewMounter(args[0], args[1], mode)
		if err != nil {
			log.Fatalln(err)
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
			log.Fatalf("failed: %v\n", err)
		}
	},
}

var pipeCmd = &cobra.Command{
	Use:     "pipe [SRC TARGET] [\"d1 | d2 | ..\"]",
	Short:   "Pipe a digi's input.x to another's output.y",
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

		//fmt.Printf("pipe %s -> %s\n", pp.Source.Name, pp.Target.Name)

		f := pp.Pipe
		if d, _ := cmd.Flags().GetBool("delete"); d {
			f = pp.Unpipe
		}
		if err = f(); err != nil {
			log.Fatalf("pipe failed: %v\n", err)
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
