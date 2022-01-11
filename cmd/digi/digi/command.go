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
	genCmd.Flags().BoolP("visual", "v", false, "Generate template for visualization")

	RootCmd.AddCommand(pullCmd)
	RootCmd.AddCommand(pushCmd)
	RootCmd.AddCommand(kindCmd)
	RootCmd.AddCommand(rmkCmd)
	kindCmd.Flags().BoolP("local", "l", false, "Show local profiles")
	rmkCmd.Flags().BoolP("all", "a", false, "Remove kind crd")

	RootCmd.AddCommand(runCmd)
	RootCmd.AddCommand(stopCmd)
	runCmd.Flags().Bool("no-alias", false, "Do not create alias to the model")
	runCmd.Flags().Bool("show-kopf-log", false, "Enable kopf logging")
	runCmd.Flags().BoolP("enable-visual", "v", false, "Enable default visualization")
	runCmd.Flags().IntP("log-level", "l", -1, "Logging level")
	stopCmd.Flags().StringP("kind", "k", "", "Digi kind")

	RootCmd.AddCommand(testCmd)
	testCmd.Flags().BoolP("clean", "c", false, "Remove test digi")
	testCmd.Flags().BoolP("mounter", "m", false, "Enable mounter in test")
	testCmd.Flags().BoolP("strict-mounter", "s", false, "Use strict mounter in test")
	testCmd.Flags().BoolP("no-alias", "n", false, "Do not create alias to the model")

	RootCmd.AddCommand(listCmd)
	RootCmd.AddCommand(checkCmd)
	RootCmd.AddCommand(watchCmd)
	RootCmd.AddCommand(editCmd)
	RootCmd.AddCommand(logCmd)
	listCmd.Flags().BoolP("all", "a", false, "Show all digis")
	checkCmd.Flags().Int8P("verbosity", "v", 0, "Output verbosity, converted to neat level (4 - v)")
	watchCmd.Flags().Float64P("interval", "i", 1, "Refresh interval")
	watchCmd.Flags().Int8P("verbosity", "v", 1, "Output verbosity, converted to neat level (4 - v)")
	editCmd.Flags().BoolP("all", "a", false, "Edit all attributes")

	RootCmd.AddCommand(aliasCmd)
	aliasCmd.AddCommand(aliasClearCmd)
	aliasCmd.AddCommand(aliasResolveCmd)

	RootCmd.AddCommand(gcCmd)
	RootCmd.AddCommand(vizCmd)

	RootCmd.AddCommand(space.RootCmd)
	RootCmd.AddCommand(lake.RootCmd)
	RootCmd.AddCommand(lake.QueryCmd)
}
