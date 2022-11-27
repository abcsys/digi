package box

import (
	"github.com/spf13/cobra"

	"digi.dev/digi/cmd/digi/space"
)

// # Create dSpace
// digi run occupancy o1 o2
// digi run room r1
// digi space mount o1 o2 r1 // define the above as a scene _kind_ and run using dbox
// 		- export and store the trace of the scene as .zng
//		- digi box commit s1 // commit from run-time setup
// # Create a scene _instance_.
// digi box run scene s1   		// emulate a new scene instance
// digi box run scene s1 --record --out home/   // run and record
// # Record live
// digi box create scene --live // create a new scene from current dSpace
// digi box record --out home/  // start recording live
// # Replay
// digi box replay home/   		// replay a trace

var RootCmd = &cobra.Command{
	Use:   "box [command]",
	Short: "Manage mocks and scenes",
}

var AttachCmd = &cobra.Command{
	Use:     "attach SRC [SRC..] TARGET",
	Short:   "Attach a mock to a scene",
	Aliases: []string{},
	Args:    cobra.MinimumNArgs(2),
	Run: func(cmd *cobra.Command, args []string) {
		space.MountCmd.Run(cmd, args)
	},
}

var ReplayCmd = &cobra.Command{
	Use:     "replay NAME",
	Short:   "Replay a scene given name",
	Aliases: []string{},
	Args:    cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
	},
}

func init() {
	RootCmd.AddCommand(AttachCmd)
	RootCmd.AddCommand(ReplayCmd)
}
