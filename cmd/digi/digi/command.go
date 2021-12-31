package digi

import (
	"log"

	"digi.dev/digi/cmd/digi/lake"
	"digi.dev/digi/cmd/digi/space"
)

func init() {
	// TBD read from cmdline flag
	log.SetFlags(0)

	RootCmd.CompletionOptions.DisableDefaultCmd = true
	RootCmd.PersistentFlags().BoolP("quiet", "q", false, "Hide output")

	RootCmd.AddCommand(initCmd)
	RootCmd.AddCommand(genCmd)
	RootCmd.AddCommand(buildCmd)
	initCmd.Flags().StringP("group", "g", "", "Model group")
	initCmd.Flags().StringP("version", "v", "", "Model version")
	initCmd.Flags().StringP("directory", "d", "", "Image directory")
	buildCmd.Flags().BoolP("no-cache", "n", false, "Do not use build cache")

	RootCmd.AddCommand(pullCmd)
	RootCmd.AddCommand(pushCmd)
	RootCmd.AddCommand(kindCmd)
	RootCmd.AddCommand(rmkCmd)

	RootCmd.AddCommand(runCmd)
	RootCmd.AddCommand(stopCmd)
	runCmd.Flags().BoolP("no-alias", "n", false, "Do not create alias to the model")
	runCmd.Flags().BoolP("show-kopf-log", "k", false, "Enable kopf logging")
	runCmd.Flags().BoolP("debug", "d", false, "Run driver in debug mode")
	stopCmd.Flags().StringP("kind", "k", "", "Digi kind")

	RootCmd.AddCommand(testCmd)
	testCmd.Flags().BoolP("clean", "c", false, "Remove test digi")
	testCmd.Flags().BoolP("mounter", "m", false, "Enable mounter in test")
	testCmd.Flags().BoolP("strict-mounter", "s", false, "Use strict mounter in test")
	testCmd.Flags().BoolP("no-alias", "n", false, "Do not create alias to the model")

	RootCmd.AddCommand(logCmd)
	RootCmd.AddCommand(listCmd)
	RootCmd.AddCommand(watchCmd)
	RootCmd.AddCommand(editCmd)
	listCmd.Flags().BoolP("all", "a", false, "Show all digis")
	watchCmd.Flags().Float64P("interval", "i", 1, "Refresh interval")
	watchCmd.Flags().Int8P("verbosity", "v", 0, "Output verbosity, converted to neat level (4 - v)")
	editCmd.Flags().BoolP("all", "a", false, "Edit all attributes")

	RootCmd.AddCommand(aliasCmd)
	aliasCmd.AddCommand(aliasClearCmd)
	aliasCmd.AddCommand(aliasResolveCmd)

	RootCmd.AddCommand(gcCmd)

	RootCmd.AddCommand(space.RootCmd)
	RootCmd.AddCommand(lake.RootCmd)
	RootCmd.AddCommand(lake.QueryCmd)
}
