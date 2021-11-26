package main

import (
	"fmt"
	"os"

	"digi.dev/digi/cmd/digi/space"
	"github.com/spf13/cobra"
)

var RootCmd = &cobra.Command{
	Use:   "ds [options] [arguments...]",
	Short: space.RootCmd.Short,
	Args:  space.RootCmd.Args,
	Run:   space.RootCmd.Run,
}

func main() {
	RootCmd.CompletionOptions.DisableDefaultCmd = true

	if err := RootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
