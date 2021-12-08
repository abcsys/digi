package main

import (
	"fmt"
	"os"

	"digi.dev/digi/cmd/digi/lake"
	"digi.dev/digi/cmd/digi/space"
)

func main() {
	RootCmd.CompletionOptions.DisableDefaultCmd = true

	RootCmd.AddCommand(initCmd)
	initCmd.Flags().StringP("group", "g", "", "Model group.")
	initCmd.Flags().StringP("version", "v", "", "Model version.")
	RootCmd.AddCommand(genCmd)
	RootCmd.AddCommand(buildCmd)

	RootCmd.AddCommand(pullCmd)
	RootCmd.AddCommand(pushCmd)
	RootCmd.AddCommand(imageCmd)
	RootCmd.AddCommand(rmiCmd)

	RootCmd.AddCommand(runCmd)
	runCmd.Flags().BoolP("local", "l", false, "Run driver in local console")
	runCmd.Flags().BoolP("no-alias", "n", false, "Do not create alias to the model")
	runCmd.Flags().BoolP("show-kopf-log", "k", false, "Enable kopf logging")
	RootCmd.AddCommand(stopCmd)
	RootCmd.AddCommand(testCmd)
	testCmd.Flags().BoolP("clean", "c", false, "Remove test digi")
	testCmd.Flags().BoolP("no-alias", "n", false, "Do not create alias to the model")
	RootCmd.AddCommand(logCmd)
	RootCmd.AddCommand(listCmd)
	RootCmd.AddCommand(watchCmd)
	watchCmd.Flags().Float64P("interval", "i", 1, "Refresh interval")
	watchCmd.Flags().Int8P("verbosity", "v", 0, "Output verbosity, converted to neat level (4 - v)")

	RootCmd.AddCommand(aliasCmd)
	aliasCmd.AddCommand(aliasClearCmd)
	aliasCmd.AddCommand(aliasResolveCmd)

	RootCmd.AddCommand(editCmd)
	RootCmd.AddCommand(space.RootCmd)
	RootCmd.AddCommand(lake.QueryCmd)
	RootCmd.AddCommand(lake.ManageCmd)
	// TBD digi kc ... forward command to kubectl

	RootCmd.PersistentFlags().BoolP("quiet", "q", false, "Hide output")
	if err := RootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
