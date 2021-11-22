package main

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
)

var RootCmd = &cobra.Command{
	Use:   "ds [options] [arguments...]",
	Short: "Manage digis in a dSpace",
}

// TBD

func main(){
	RootCmd.CompletionOptions.DisableDefaultCmd = true

	if err := RootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}

