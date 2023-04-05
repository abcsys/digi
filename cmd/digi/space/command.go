package space

import (
	"fmt"
	"log"

	"github.com/spf13/cobra"

	"digi.dev/digi/api"
	"digi.dev/digi/api/k8s"
	"digi.dev/digi/cmd/digi/helper"
	"digi.dev/digi/space"
)

const DefaultMountRetry = 3

var (
	controllers = map[string]bool{
		"lake":    true,
		"syncer":  true,
		"mounter": true,
		"emqx":    true,
		"net":     true,
		"sourcer": true,
		// ...
	}
)

var RootCmd = &cobra.Command{
	Use:   "space [command]",
	Short: "Manage the dSpace",
}

var MountCmd = &cobra.Command{
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
		numRetry, _ := cmd.Flags().GetInt("num-retry")

		mt, err := api.NewMounter(sources, target, op, mode, numRetry)
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
		registryFile, _ := cmd.Flags().GetString("registry-file")
		params := map[string]string{
			"CR": registryFile,
		}

		if len(args) == 0 {
			_ = helper.RunMake(params, "start-space", true, false)
		} else {
			for _, name := range args {
				if ok, _ := controllers[name]; !ok {
					log.Fatalf("unknown controller: %s\n", name)
				}
				_ = StartControllerWithParams(params, name)
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
				_ = StopController(name)
			}
		}
	},
}

func StartController(name string) error {
	return helper.RunMake(nil, "start-"+name, true, false)
}

func StartControllerWithParams(params map[string]string, name string) error {
	return helper.RunMake(params, "start-"+name, true, false)
}

func StopController(name string) error {
	return helper.RunMake(nil, "stop-"+name, true, false)
}

var registerCmd = &cobra.Command{
	Use:     "register REGISTRY USER",
	Short:   "register the current dSpace on the given registry",
	Aliases: []string{"register"},
	Args:    cobra.ExactArgs(2),
	Run: func(cmd *cobra.Command, args []string) {
		// TBD the register command should go through a proxy without
		//	sharing the cluster's access credentials with the registry;
		//	registry's commands such as /list should be run by the proxy.
		kc, err := k8s.LoadKubeConfig()
		if err != nil {
			log.Fatal("Failed to load config from Kube Config file.")
		}
		context := k8s.CurrentContext(kc)
		if exists, err := k8s.ClusterExistsLocal(context); !exists || err != nil {
			log.Fatal("Cluster for current context ", context, " not found.")
		}
		cluster := kc.Clusters[context]
		apiserver := cluster.Server
		user := kc.AuthInfos[context]
		caCrt := cluster.CertificateAuthority
		clientCrt := user.ClientCertificate
		clientKey := user.ClientKey
		_ = helper.RunMake(map[string]string{
			"ADDR":       args[0],
			"USER":       args[1],
			"APISERVER":  apiserver,
			"CONTEXT":    context,
			"CA.CRT":     caCrt,
			"CLIENT.CRT": clientCrt,
			"CLIENT.KEY": clientKey,
		}, "register-space", true, false)
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
	Use:     "use NAME",
	Short:   "Switch to a digi space",
	Aliases: []string{"checkout", "u", "switch"},
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

var addCmd = &cobra.Command{
	Use:   "add CONFIG",
	Short: "Add a digi space from given config file",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		force, _ := cmd.Flags().GetBool("force")
		root, err := k8s.LoadKubeConfig()
		if err != nil {
			log.Fatal("Failed to load config from root Kube Config file.")
		}

		given, err := k8s.LoadKubeConfig(args[0])
		if err != nil {
			log.Fatal("Failed to load config from the given Kube Config file.")
		}

		if !force {
			// check if the clusters in the give config already exist in the root config
			rootClusters := k8s.Clusters(root)
			for _, cluster := range k8s.Clusters(given) {
				if contains(rootClusters, cluster) {
					log.Fatal("Cluster ", cluster, " already exists in the root; rename or use -f.")
				}
			}

			// check if the contexts in the given config already exists in the root config
			rootContexts := k8s.Contexts(root)
			for _, context := range k8s.Contexts(given) {
				if contains(rootContexts, context) {
					log.Fatal("Context ", context, " already exists in the root; rename or use -f.")
				}
			}

			// check if the user in the given config already exists in the root config
			rootUsers := k8s.Users(root)
			for _, user := range k8s.Users(given) {
				if contains(rootUsers, user) {
					log.Fatal("User ", user, " already exists in the root; rename or use -f.")
				}
			}
		}

		// merge the given config into the root config; root takes precedence
		merged, err := k8s.MergeKubeConfigs(root, given)
		if err != nil {
			log.Fatal("Failed to merge Kube Config files.")
		}

		if err = k8s.WriteKubeConfig(merged); err != nil {
			log.Fatal("Failed to write merged Kube Config file.")
		}
	},
}

// delete a space from the root config
var deleteCmd = &cobra.Command{
	Use:     "delete NAME",
	Short:   "Delete a digi space from local access",
	Aliases: []string{"del", "remove"},
	Args:    cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		root, err := k8s.LoadKubeConfig()
		if err != nil {
			log.Fatal("Failed to load config from root Kube Config file.")
		}

		// check if the space exists in the root config
		if !contains(k8s.Contexts(root), args[0]) {
			log.Fatal("Space ", args[0], " does not exist in the root.")
		}

		// delete the space from the root config
		err = k8s.DeleteKubeConfig(root, args[0])
		if err != nil {
			log.Fatal("Failed to delete space ", args[0], " from the root.")
		}

		if err = k8s.WriteKubeConfig(root); err != nil {
			log.Fatal("Failed to write merged Kube Config file.")
		}
	},
}

func contains(strs []string, str string) bool {
	for _, s := range strs {
		if s == str {
			return true
		}
	}
	return false
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

var gcCmd = &cobra.Command{
	Use:     "gc",
	Short:   "Run garbage collection",
	Aliases: []string{"clean"},
	Args:    cobra.ExactArgs(0),
	Run: func(cmd *cobra.Command, args []string) {
		_ = helper.RunMake(map[string]string{}, "gc", true, false)
	},
}

func init() {
	log.SetFlags(0)
	// TBD delete digi space removes all running digis and controllers
	RootCmd.AddCommand(startCmd)
	startCmd.Flags().StringP("registry-file", "f", "cr.yaml", "Specify a file containing registry data")
	RootCmd.AddCommand(stopCmd)

	RootCmd.AddCommand(MountCmd)
	MountCmd.Flags().BoolP("delete", "d", false, "Unmount source from target")
	MountCmd.Flags().BoolP("yield", "y", false, "Yield a mount")
	MountCmd.Flags().BoolP("activate", "a", false, "Activate a mount")
	MountCmd.Flags().StringP("mode", "m", space.DefaultMountMode, "Set mount mode")
	MountCmd.Flags().IntP("num-retry", "n", DefaultMountRetry, "Set mount mode")

	RootCmd.AddCommand(pipeCmd)
	pipeCmd.Flags().BoolP("delete", "d", false, "Unpipe source from target")

	RootCmd.AddCommand(registerCmd)
	RootCmd.AddCommand(listCmd)
	RootCmd.AddCommand(checkCmd)
	RootCmd.AddCommand(switchCmd)
	RootCmd.AddCommand(addCmd)
	addCmd.Flags().BoolP("force", "f", false, "Force add space, ignoring conflicts")
	RootCmd.AddCommand(deleteCmd)
	RootCmd.AddCommand(aliasCmd)
	RootCmd.AddCommand(gcCmd)
	listCmd.Flags().BoolP("current", "c", false, "List current space")
}
