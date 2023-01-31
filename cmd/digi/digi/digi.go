package digi

import (
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"sync"

	"github.com/spf13/cobra"

	"digi.dev/digi/api"
	"digi.dev/digi/api/config"
	"digi.dev/digi/api/repo"
	"digi.dev/digi/cmd/digi/helper"
	"digi.dev/digi/pkg/core"
)

var (
	RootCmd = &cobra.Command{
		Use:   "digi <command> [options] [arguments...]",
		Short: "command line digi manager",
		Long: `
    Command-line digi manager.
    `,
	}
)

var configCmd = &cobra.Command{
	Use:     "config",
	Short:   "Configure the default parameters for Digi CLI",
	Aliases: []string{"configure"},
	Args:    cobra.ExactArgs(0),
	Run: func(cmd *cobra.Command, args []string) {
		var repo, driverRepo string

		if clear, _ := cmd.Flags().GetBool("clear"); clear {
			_ = config.ClearConfig()
		}

		if repo, _ := cmd.Flags().GetString("repo"); repo != "" {
			if err := config.Set("REPO", repo); err != nil {
				fmt.Printf("unable to set digi repo: %s", err)
			}
		}

		if driverRepo, _ := cmd.Flags().GetString("driver-repo"); driverRepo != "" {
			if err := config.Set("DRIVER_REPO", driverRepo); err != nil {
				fmt.Printf("unable to set driver repo: %s", err)
			}
		}
		// ...

		if repo == "" && driverRepo == "" {
			config.ShowAll()
		}
	},
}

var initCmd = &cobra.Command{
	Use:     "init KIND",
	Short:   "Initialize a new kind",
	Long:    "Create a digi template with the directory name defaults to the kind",
	Aliases: []string{"i"},
	Args:    cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")

		kind := args[0]
		params := map[string]string{
			"KIND": strings.Title(kind),
			// default configs
			"GROUP":   "digi.dev",
			"VERSION": "v1",
			"PROFILE": kind,
		}

		if g, _ := cmd.Flags().GetString("group"); g != "" {
			params["GROUP"] = g
		}
		if v, _ := cmd.Flags().GetString("version"); v != "" {
			params["VERSION"] = v
		}
		if d, _ := cmd.Flags().GetString("directory"); d != "" {
			params["PROFILE"] = d
		}

		_ = helper.RunMake(params, "init", true, q)
		if !q {
			fmt.Println(kind)
		}
	},
}

var genCmd = &cobra.Command{
	Use:     "gen KIND [KIND ...]",
	Short:   "Generate configs for a kind",
	Aliases: []string{"g"},
	Args:    cobra.MinimumNArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")
		tag, _ := cmd.Flags().GetString("tag")
		params := make(map[string]string)
		if v, _ := cmd.Flags().GetBool("visual"); v {
			params["GENFLAG"] = "VISUAL=true"
		}

		driverRepo, _ := config.Get("DRIVER_REPO")

		for _, profile := range args {
			profile = strings.TrimSpace(profile)
			params := map[string]string{
				"PROFILE":    profile,
				"DRIVER_TAG": tag,
			}
			if driverRepo != "" {
				params["DRIVER_REPO"] = driverRepo
			}
			if _ = helper.RunMake(params, "gen", true, q); !q {
				fmt.Println(profile)
			}
		}
	},
}

var buildCmd = &cobra.Command{
	Use:     "build KIND [KIND ...]",
	Short:   "Build a kind",
	Aliases: []string{"b"},
	Args:    cobra.MinimumNArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")
		noCache, _ := cmd.Flags().GetBool("no-cache")
		platform, _ := cmd.Flags().GetString("platform")
		all, _ := cmd.Flags().GetBool("all-platforms")
		tag, _ := cmd.Flags().GetString("tag")
		imageFile, _ := cmd.Flags().GetString("image")
		digiliteFile, _ := cmd.Flags().GetString("digilite")

		platforms := make(map[string]bool)
		if all {
			platforms = api.Platforms
		} else {
			platforms[platform] = true
		}

		driverRepo, _ := config.Get("DRIVER_REPO")

		for _, profile := range args {
			profile = strings.TrimSpace(profile)
			kind, err := helper.GetKindFromProfile(profile)
			if err != nil {
				log.Fatalf("unable to find kind %s\n", profile)
			}

			params := map[string]string{
				"GROUP":      kind.Group,
				"VERSION":    kind.Version,
				"KIND":       kind.Name,
				"PROFILE":    profile,
				"DRIVER_TAG": tag,
				"DOCKERFILE": imageFile,
			}
			if driverRepo != "" {
				params["DRIVER_REPO"] = driverRepo
			}

			if digiliteFile != "" {
				if imageFile != "" {
					log.Printf("WARNING: Digilite file is declared, \"%s\" will be overwritten with \"%s\"\n", imageFile, digiliteFile)
				}
				digilitePath := filepath.Join(os.Getenv("GOPATH"), "src/digi.dev/digilite", digiliteFile, "Dockerfile")
				if fileInfo, err := os.Stat(digilitePath); !os.IsNotExist(err) && !fileInfo.IsDir() {
					params["DOCKERFILE"] = digilitePath
				} else {
					log.Fatalf("error building %s: Digilite path of \"%s\" does not exist", kind.Name, digilitePath)
					return
				}
			} else {
				if imageFile != "" {
					workDir, err := os.Getwd()
					if err != nil {
						log.Fatalf("error building %s: %v", kind.Name, err)
						return
					}

					imagePaths := []string{
						filepath.Join(workDir, imageFile, "Dockerfile"),
						filepath.Join(workDir, imageFile),
					}

					pathFound := false

					for _, imagePath := range imagePaths {
						if fileInfo, err := os.Stat(imagePath); !os.IsNotExist(err) && !fileInfo.IsDir() {
							params["DOCKERFILE"] = imagePath
							pathFound = true
							break
						}
					}

					if !pathFound {
						log.Fatalf("error building %s: Image path does not exist", kind.Name)
						return
					}
				}
			}

			// clear manifest cache
			_ = helper.RunMake(params, "clear-manifest", true, q)

			for platform := range platforms {
				var buildFlag, pushFlag string
				if q {
					buildFlag += " -q"
					pushFlag += " -q"
				}
				if noCache {
					buildFlag += " --no-cache"
				}

				// multi-platform build
				var arch string
				if platform != "" {
					buildFlag += fmt.Sprintf(" --platform %s", platform)
					// e.g., linux/amd64 -> amd64; linux/arm/v7 -> arm-v7
					arch = platform[strings.Index(platform, "/")+1:]
					arch = strings.ReplaceAll(arch, "/", "-")
				}

				params["BUILDFLAG"] = buildFlag
				params["PUSHFLAG"] = pushFlag
				if arch != "" {
					params["ARCH"] = arch
				}

				if err := helper.RunMake(params, "build", true, q); err == nil {
					fmt.Println(kind.Name)
				} else {
					log.Fatalf("error building %s: %v", kind.Name, err)
				}
			}
		}
	},
}

var kindCmd = &cobra.Command{
	Use:     "kind",
	Short:   "List available kinds",
	Aliases: []string{"kinds", "profile", "profiles", "k", "p"},
	Args:    cobra.ExactArgs(0),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")
		l, _ := cmd.Flags().GetBool("local")
		if !q {
			fmt.Println("KIND")
		}
		cmdStr := "profile"
		if l {
			cmdStr = "profile-local"
		}
		_ = helper.RunMake(nil, cmdStr, true, false)
	},
}

var pullCmd = &cobra.Command{
	Use:   "pull KIND [KIND ...]",
	Short: "Pull a kind",
	Args:  cobra.MinimumNArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")
		local, _ := cmd.Flags().GetBool("local")
		group, _ := cmd.Flags().GetString("group")

		var wg sync.WaitGroup
		for _, name := range args {
			wg.Add(1)
			go func(name string) {
				defer wg.Done()
				// TBD local repo
				if local {
					err := helper.RunMake(map[string]string{
						"PROFILE_NAME": name,
					}, "pull", false, q)
					if err != nil {
						log.Fatalf("unable to pull %s: %v\n", name, err)
					} else if !q {
						log.Println(name)
					}
				} else {
					// GitHub
					kind, err := core.KindFromString(name)
					if group != "" {
						kind.Group = group
					}
					if err != nil {
						log.Fatalf("unable to parse %s to kind: %v\n", name, err)
						return
					}
					err = repo.Pull(kind)
					if err != nil {
						log.Fatalf("unable to pull %s: %v\n from remote", name, err)
						return
					}
					fmt.Println(name)
				} // ... other repo types
			}(name)
		}
		wg.Wait()
	},
}

var pushCmd = &cobra.Command{
	Use:   "push KIND",
	Short: "Push a kind",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")

		profile := args[0]
		kind, err := helper.GetKindFromProfile(profile)
		if err != nil {
			log.Fatalf("unable to find kind %s\n", profile)
		}

		if _ = helper.RunMake(map[string]string{
			"GROUP":   kind.Group,
			"VERSION": kind.Version,
			"KIND":    kind.Name,
			"PROFILE": profile,
		}, "push", true, q); !q {
			fmt.Println(kind)
		}
	},
}

var commitCmd = &cobra.Command{
	Use:   "commit NAME [NAME ...]",
	Short: "Generate a snapshot for given digis",
	Args:  cobra.MinimumNArgs(1),
	Run: func(cmd *cobra.Command, args []string) {

		var workDir string
		if workDir = os.Getenv("WORKDIR"); workDir == "" {
			workDir = "."
		}

		var targetDir string
		targetDir, _ = cmd.Flags().GetString("targetDir")
		if targetDir == "" {
			targetDir = workDir
		}

		paths, _ := cmd.Flags().GetStringSlice("paths")
		addpaths := strings.Join(paths, ",")
		pathlist := fmt.Sprintf("[%s]", addpaths)

		for _, name := range args {
			_, err := api.Resolve(name)
			if err != nil {
				log.Fatalf("unknown digi kind from alias given name %s: %v\n", name, err)
			}
		}

		for _, name := range args {
			duri, err := api.Resolve(name)
			kind := duri.Kind

			params := map[string]string{
				"GROUP":     kind.Group,
				"VERSION":   kind.Version,
				"KIND":      kind.Name,
				"PLURAL":    kind.Plural(),
				"NAME":      name,
				"TARGETDIR": targetDir,
				"NEATLEVEL": fmt.Sprintf("-l %d", 4),
				"NAMESPACE": "default",
				"ADDPATHS":  pathlist,
			}
			if len(args) > 1 {
				fmt.Printf("%s:\n", name)
			}

			if err == nil {
				currStdout := os.Stdout
				r, w, _ := os.Pipe()
				os.Stdout = w

				_ = helper.RunMake(params, "generation", true, false)

				w.Close()
				captured, _ := ioutil.ReadAll(r)
				os.Stdout = currStdout

				params["GEN"] = strings.TrimSpace(string(captured))

				fmt.Printf("%s_snapshot_gen%s\n", params["NAME"], params["GEN"])
				_ = helper.RunMake(params, "commit", true, false)
			}
		}
	},
}

var digestCmd = &cobra.Command{
	Use:   "digest NAME",
	Short: "Compute the digest for a digi or a kind",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {

		//check if args[0] is a snapshot directory
		var workDir string
		if workDir = os.Getenv("WORKDIR"); workDir == "" {
			workDir = "."
		}
		intentStatusYamlPath := fmt.Sprintf("%s/%s/spec.yaml", workDir, args[0])
		_, err := os.Stat(intentStatusYamlPath)
		isSnapshotDir := err == nil

		if isSnapshotDir {
			params := map[string]string{
				"DIRNAME": args[0],
			}

			_ = helper.RunMake(params, "checksum-snapshot", true, false)
		} else {
			for _, name := range args {
				duri, err := api.Resolve(name)
				kind := duri.Kind

				params := map[string]string{
					"GROUP":     kind.Group,
					"VERSION":   kind.Version,
					"KIND":      kind.Name,
					"PLURAL":    kind.Plural(),
					"NAME":      name,
					"NEATLEVEL": fmt.Sprintf("-l %d", 4),
					"NAMESPACE": "default",
				}
				if len(args) > 1 {
					fmt.Printf("%s:\n", name)
				}

				if err == nil {
					_ = helper.RunMake(params, "checksum-digi", true, false)
				}
			}
		}
	},
}

var testCmd = &cobra.Command{
	Use:     "test KIND",
	Short:   "Test run a digi's driver",
	Aliases: []string{"t"},
	Args:    cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		var name, profile string

		profile = args[0]
		kind, err := helper.GetKindFromProfile(profile)
		if err != nil {
			log.Fatalf("unable to find kind %s\n", profile)
		}

		name = kind.Name

		var useMounter, useStrictMounter string
		if um, _ := cmd.Flags().GetBool("mounter"); um {
			useMounter = "true"
		} else {
			useMounter = "false"
		}

		if um, _ := cmd.Flags().GetBool("strict-mounter"); um {
			useStrictMounter = "true"
		} else {
			useStrictMounter = "false"
		}

		params := map[string]string{
			"PROFILE":      profile,
			"GROUP":        kind.Group,
			"VERSION":      kind.Version,
			"KIND":         kind.Name,
			"PLURAL":       kind.Plural(),
			"NAME":         name,
			"NAMESPACE":    "default",
			"MOUNTER":      useMounter,
			"STRICT_MOUNT": useStrictMounter,
		}

		if noAlias, _ := cmd.Flags().GetBool("no-alias"); !noAlias {
			// create alias beforehand because the test will hang
			if err := helper.CreateAlias(kind, name, "default"); err != nil {
				log.Fatalf("unable to create alias: %v\n", err)
			}
			// TBD defer remove alias
		}

		var cmdStr string
		c, _ := cmd.Flags().GetBool("clean")
		if cmdStr = "test"; c {
			cmdStr = "clean-test"
		}

		_ = helper.RunMake(params, cmdStr, true, false)
	},
}

var logCmd = &cobra.Command{
	Use:     "log NAME",
	Short:   "Print log of a digi's driver",
	Aliases: []string{"logs", "l"},
	Args:    cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")

		name := args[0]
		_ = helper.RunMake(map[string]string{
			"NAME": name,
		}, "log", true, q)
	},
}

var editCmd = &cobra.Command{
	Use:     "edit NAME",
	Short:   "Edit a digi's model",
	Aliases: []string{"e"},
	Args:    cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		editAll, _ := cmd.Flags().GetBool("all")

		// TBD allow namespace
		// TBD do not filter resource version, gen, and assign to neat level 2
		var name string

		name = args[0]
		duri, err := api.Resolve(name)
		if err != nil {
			log.Fatalf("unable to resolve digi name %s: %v\n", name, err)
		}

		var cmdStr string
		if cmdStr = "edit"; editAll {
			cmdStr = "edit-all"
		}

		f, err := os.CreateTemp("", "digi-edit-"+name)
		if err != nil {
			log.Fatalln(err)
		}
		if err = f.Close(); err != nil {
			log.Fatalln(err)
		}
		path := f.Name()
		_ = helper.RunMake(map[string]string{
			"GROUP":  duri.Kind.Group,
			"KIND":   duri.Kind.Name,
			"PLURAL": duri.Kind.Plural(),
			"NAME":   name,
			"FILE":   path,
		}, cmdStr, true, false)
		_ = os.Remove(path)
	},
}

var runCmd = &cobra.Command{
	Use:   "run KIND NAME [NAME ...]",
	Short: "Run a digi given kind and name",
	Long: "Run a digi given kind and name; more than one name can be given. " +
		"The kind should be accessible in current path.\n" +
		"You can use bash range notation({a..b}) to run multiple digis at once. Ex. digi run lamp l{1..9}, will start l1-l9 lamps.",
	Aliases: []string{"r"},
	// TBD enable passing namespace
	Args: cobra.MinimumNArgs(2),
	Run: func(cmd *cobra.Command, args []string) {
		var profile = args[0]
		kind, err := helper.GetKindFromProfile(profile)
		if err != nil {
			log.Fatalf("unable to find kind %s: %v\n", profile, err)
		}

		var names []string
		names = args[1:]

		//check if args[0] is a snapshot directory
		var workDir string
		if workDir = os.Getenv("WORKDIR"); workDir == "" {
			workDir = "."
		}
		intent_status_yaml_path := fmt.Sprintf("%s/%s/spec.yaml", workDir, args[0])
		_, err = os.Stat(intent_status_yaml_path)
		isSnapshotDir := err == nil

		var suffix string
		suffix, _ = cmd.Flags().GetString("childSuffix")

		//if args[0] is a snapshot directory, make sure none of the other arguments correspond to names of existing digis
		if isSnapshotDir {
			currAPIClient, err := api.NewClient()
			if err != nil {
				log.Fatalf("Error creating API Client\n")
			}

			for _, name := range names {
				name = strings.TrimSpace(name)
				currAuri, err := api.Resolve(name)

				if err == nil && currAuri != nil {
					json, _ := currAPIClient.GetModelJson(currAuri)
					if len(json) > 0 {
						log.Fatalf("Digi name conflict: %s already exists\n", name)
					}
				}
			}
		}

		quiet, _ := cmd.Flags().GetBool("quiet")
		noAlias, _ := cmd.Flags().GetBool("no-alias")
		logLevel, _ := cmd.Flags().GetInt("log-level")
		visual, _ := cmd.Flags().GetBool("enable-visual")
		deployFile, _ := cmd.Flags().GetString("deploy-file")
		persistentVolume, _ := cmd.Flags().GetBool("persistent-volume")

		kopfLog := "false"
		if k, _ := cmd.Flags().GetBool("kopf-log"); k {
			kopfLog = "true"
		}
		cmdStr := "run"
		if np, _ := cmd.Flags().GetBool("no-pool"); np {
			cmdStr = "run-no-pool"
		}

		var runFlag string
		switch {
		case logLevel < 0: // unset
		case logLevel < 20: // debug
			runFlag += " --set trim_mount_on_load=false"
			fallthrough
		default:
			runFlag += " --set log_level=" + strconv.Itoa(logLevel)
		}
		if visual {
			runFlag += " --set visual=true"
		}

		if persistentVolume {
			persistentVolumeSize, _ := cmd.Flags().GetString("pv-size")
			persistentVolumePath, _ := cmd.Flags().GetString("pv-path")
			runFlag += fmt.Sprintf(" --set persistent_volume.path=%s,persistent_volume.size=%s", persistentVolumePath, persistentVolumeSize)
		}

		var wg sync.WaitGroup
		logger := log.New(os.Stdout, "", 0)

		for _, name := range names {
			name = strings.TrimSpace(name)

			wg.Add(1)
			go func(name string, quiet bool) {
				defer wg.Done()
				if err := helper.RunMake(map[string]string{
					"PROFILE": profile,
					"GROUP":   kind.Group,
					"VERSION": kind.Version,
					"KIND":    kind.Name,
					"PLURAL":  kind.Plural(),
					"NAME":    name,
					"KOPFLOG": kopfLog,
					"RUNFLAG": runFlag,
					"CR":      deployFile,
				}, cmdStr, false, quiet); err == nil {
					if !noAlias {
						// TBD check potential race
						err := helper.CreateAlias(kind, name, "default")
						if err != nil {
							logger.Println("unable to create alias")
						}
					}
				}
			}(name, quiet)
		}
		wg.Wait()

		if isSnapshotDir {
			for _, name := range names {
				if suffix == "" {
					suffix = "[]"
				}

				name = strings.TrimSpace(name)
				params := map[string]string{
					"GROUP":     kind.Group,
					"VERSION":   kind.Version,
					"KIND":      kind.Name,
					"DIRNAME":   args[0],
					"PLURAL":    kind.Plural(),
					"NAME":      name,
					"SUFFIX":    suffix,
					"NEATLEVEL": fmt.Sprintf("-l %d", 4),
					"NAMESPACE": "default",
				}
				if len(args) > 2 {
					fmt.Printf("%s:\n", name)
				}

				_ = helper.RunMake(params, "recreate", true, false)
			}
		}
	},
}

var stopCmd = &cobra.Command{
	Use:   "stop NAME [NAME ...]",
	Short: "Stop a digi given the name",
	Long: "Stop a digi given the name.\n" +
		"You can use bash range notation({a..b}) to stop multiple digis at once. Ex. digi stop lamp l{1..9}, will stop l1-l9 lamps.",
	Aliases: []string{"s"},
	Args:    cobra.MinimumNArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		quiet, _ := cmd.Flags().GetBool("quiet")
		kindStr, _ := cmd.Flags().GetString("kind")

		// TBD handle namespace
		var kind *core.Kind
		if kindStr != "" {
			var err error
			if kind, err = core.KindFromString(kindStr); err != nil {
				log.Fatalf("unable to parse kind %s: %v\n", kindStr, err)
			}
		}

		var wg sync.WaitGroup

		for _, name := range args {
			name = strings.TrimSpace(name)
			if kindStr == "" {
				duri, err := api.Resolve(name)
				if err != nil {
					log.Fatalf("unknown digi kind from alias given name %s\n", name)
				}
				kind = &duri.Kind
			}

			wg.Add(1)
			go func(name string, quiet bool) {
				defer wg.Done()
				_ = helper.RunMake(map[string]string{
					"GROUP":   kind.Group,
					"VERSION": kind.Version,
					"KIND":    kind.Name,
					"PLURAL":  kind.Plural(),
					"NAME":    name,
				}, "stop", false, quiet)
			}(name, quiet)
		}
		wg.Wait()
	},
}

var rmkCmd = &cobra.Command{
	Use:     "rmk KIND [KIND ...]",
	Short:   "Remove a kind locally",
	Aliases: []string{"rmi"},
	Args:    cobra.MinimumNArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")
		a, _ := cmd.Flags().GetBool("all")
		var cmdStr string
		if cmdStr = "delete"; a {
			cmdStr = "delete-all"
		}

		var wg sync.WaitGroup
		for _, name := range args {
			wg.Add(1)
			go func(name string) {
				defer wg.Done()
				_ = helper.RunMake(map[string]string{
					"PROFILE": name,
				}, cmdStr, false, q)
			}(name)
		}
		wg.Wait()
	},
}

var (
	aliasCmd = &cobra.Command{
		Use:   "alias [AURI ALIAS]",
		Short: "Create a digi alias",
		Args:  cobra.MaximumNArgs(2),
		Run: func(cmd *cobra.Command, args []string) {
			if len(args) == 0 {
				if err := api.ShowAll(); err != nil {
					log.Fatalln(err)
				}
				return
			}

			if len(args) == 1 {
				log.Fatalln("args should be either none or 2")
			}

			// parse the duri
			duri, err := api.ParseAuri(args[0])
			if err != nil {
				log.Fatalf("unable to parse duri %s: %v\n", args[0], err)
			}

			a := &api.Alias{
				Auri: &duri,
				Name: args[1],
			}

			if err := a.Set(); err != nil {
				log.Fatalln("unable to set alias: ", err)
			}
		},
	}
	aliasClearCmd = &cobra.Command{
		Use:   "clear",
		Short: "Clear all aliases",
		Args:  cobra.ExactArgs(0),
		Run: func(cmd *cobra.Command, args []string) {
			if err := api.ClearAlias(); err != nil {
				log.Fatalln("unable to clear alias: ", err)
			}
		},
	}
	aliasResolveCmd = &cobra.Command{
		Use:   "resolve ALIAS",
		Short: "Resolve an alias",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			if err := api.ResolveFromLocal(args[0]); err != nil {
				log.Fatalf("unable to resolve alias %s: %v\n", args[0], err)
			}
		},
	}
)

var listCmd = &cobra.Command{
	Use:   "list [SCOPE]",
	Short: "Get a list of running digis",
	Long: `
The list command returns a list of running digis. If the optional 
scope is given, the returned digis are limited to the scope in the
form of, e.g., r1.lamp. The scope is parsed using the local 
alias cache.
`,
	Aliases: []string{"ls"},
	Args:    cobra.MaximumNArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")
		showAll, _ := cmd.Flags().GetBool("all")
		if !q {
			fmt.Println("NAME")
		}
		flags := ""
		if !showAll {
			flags += " -l app!=lake,app!=syncer,app!=emqx"
		}
		if len(args) == 0 {
			_ = helper.RunMake(map[string]string{
				"FLAG": flags,
			}, "list", true, false)
		} else {

		}
	},
}

var checkCmd = &cobra.Command{
	Use:     "check NAME [NAME ...]",
	Short:   "Print a digi's model",
	Aliases: []string{"c", "show"},
	Args:    cobra.MinimumNArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		v, _ := cmd.Flags().GetInt8("verbosity")
		for _, name := range args {
			duri, err := api.Resolve(name)
			if err != nil {
				log.Fatalf("unknown digi kind from alias given name %s: %v\n", name, err)
			}
			kind := duri.Kind

			params := map[string]string{
				"GROUP":   kind.Group,
				"VERSION": kind.Version,
				"KIND":    kind.Name,
				"PLURAL":  kind.Plural(),
				"NAME":    name,
				// TBD get max neat level from kubectl-neat
				"NEATLEVEL": fmt.Sprintf("-l %d", 4-v),
			}
			if len(args) > 1 {
				fmt.Printf("%s:\n", name)
			}
			_ = helper.RunMake(params, "check", true, false)
		}
	},
}

var watchCmd = &cobra.Command{
	Use:     "watch NAME [NAME ...]",
	Short:   "Watch changes of a digi's model",
	Aliases: []string{"w"},
	Args:    cobra.MinimumNArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		i, _ := cmd.Flags().GetFloat32("interval")
		v, _ := cmd.Flags().GetInt8("verbosity")

		names := strings.Join(args, " ")
		params := map[string]string{
			"NAME":     names,
			"INTERVAL": fmt.Sprintf("%f", i),
			// XXX v is passed to check command as verbosity
			"NEATLEVEL": fmt.Sprintf("%d", v),
		}

		_ = helper.RunMake(params, "watch", true, false)
	},
}

var vizCmd = &cobra.Command{
	Use:     "visualize [NAME]",
	Short:   "Visualize a digi",
	Aliases: []string{"viz", "vis", "vz", "v"},
	Run: func(cmd *cobra.Command, args []string) {
		var cmdStr string
		var params map[string]string
		if len(args) > 0 {
			port := helper.GetPort()
			params = map[string]string{
				"NAME":      args[0],
				"LOCALPORT": strconv.Itoa(port),
			}
			cmdStr = "viz"
		} else {
			cmdStr = "viz-space"
		}
		_ = helper.RunMake(params, cmdStr, true, false)
	},
}
