package digi

import (
	"digi.dev/digi/cmd/digi/lake"
	"digi.dev/digi/cmd/digi/space"
)

func init() {
	RootCmd.CompletionOptions.DisableDefaultCmd = true
	RootCmd.PersistentFlags().BoolP("quiet", "q", false, "Hide output")

	RootCmd.AddCommand(initCmd)
	initCmd.Flags().StringP("group", "g", "", "Model group.")
	initCmd.Flags().StringP("version", "v", "", "Model version.")
	initCmd.Flags().StringP("directory", "d", "", "Image directory.")
	RootCmd.AddCommand(genCmd)
	RootCmd.AddCommand(buildCmd)

	RootCmd.AddCommand(pullCmd)
	RootCmd.AddCommand(pushCmd)
	RootCmd.AddCommand(imageCmd)
	RootCmd.AddCommand(rmkCmd)

	RootCmd.AddCommand(runCmd)
	runCmd.Flags().BoolP("local", "l", false, "Run driver in local console")
	runCmd.Flags().BoolP("no-alias", "n", false, "Do not create alias to the model")
	runCmd.Flags().BoolP("show-kopf-log", "k", false, "Enable kopf logging")
	RootCmd.AddCommand(stopCmd)
	RootCmd.AddCommand(testCmd)
	testCmd.Flags().BoolP("clean", "c", false, "Remove test digi")
	testCmd.Flags().BoolP("mounter", "m", false, "Enable mounter in test")
	testCmd.Flags().BoolP("strict-mounter", "s", false, "Use strict mounter in test")
	testCmd.Flags().BoolP("no-alias", "n", false, "Do not create alias to the model")
	RootCmd.AddCommand(logCmd)
	RootCmd.AddCommand(listCmd)
	listCmd.Flags().BoolP("all", "a", false, "Show all digis")
	RootCmd.AddCommand(editCmd)
	RootCmd.AddCommand(watchCmd)
	watchCmd.Flags().Float64P("interval", "i", 1, "Refresh interval")
	watchCmd.Flags().Int8P("verbosity", "v", 0, "Output verbosity, converted to neat level (4 - v)")
	RootCmd.AddCommand(gcCmd)

	RootCmd.AddCommand(aliasCmd)
	aliasCmd.AddCommand(aliasClearCmd)
	aliasCmd.AddCommand(aliasResolveCmd)

	RootCmd.AddCommand(space.RootCmd)
	RootCmd.AddCommand(lake.QueryCmd)
	RootCmd.AddCommand(lake.RootCmd)
}
