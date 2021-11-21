package main

import (
	"bytes"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	"digi.dev/digi/api"
	"digi.dev/digi/pkg/core"
	"github.com/spf13/cobra"
	"gopkg.in/yaml.v2"
)

var (
	RootCmd = &cobra.Command{
		Use:   "digi [command]",
		Short: "command line digi manager",
		Long: `
    Command-line digi manager.
    `,
	}
	homeDir string
)

func init() {
	var err error
	homeDir, err = os.UserHomeDir()
	if err != nil {
		panic(err)
	}
	homeDir = filepath.Join(homeDir, ".dq")
}

func runMake(args map[string]string, cmd string, quiet bool) error {
	cmd_ := exec.Command("make", "-s", "--ignore-errors", cmd)
	cmd_.Env = os.Environ()

	for k, v := range args {
		cmd_.Env = append(cmd_.Env,
			fmt.Sprintf("%s=%s", k, v),
		)
	}

	if os.Getenv("WORKDIR") == "" {
		curDir, err := os.Getwd()
		if err != nil {
			panic(err)
		}
		cmd_.Env = append(cmd_.Env,
			fmt.Sprintf("WORKDIR=%s", curDir),
		)
	}
	cmd_.Dir = homeDir

	var out bytes.Buffer
	cmd_.Stdout = os.Stdout
	cmd_.Stdout = &out
	cmd_.Stderr = &out

	if err := cmd_.Run(); err != nil {
		log.Fatalf("error: %v\n%s", err, out.String())
		return err
	}

	if !quiet {
		fmt.Print(out.String())
	}

	if strings.Contains(
		strings.ToLower(out.String()),
		"error",
	) {
		return fmt.Errorf("%s\n", out.String())
	}

	// TBD streaming output
	return nil
}

var initCmd = &cobra.Command{
	Use:   "init KIND",
	Short: "Initialize a digi template",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")

		kind := args[0]
		if err := runMake(map[string]string{
			"KIND": kind,
		}, "init", q); err == nil && !q {
			fmt.Println(kind)
		}
	},
}

var genCmd = &cobra.Command{
	Use:   "gen KIND",
	Short: "Generate files in a digi image",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")

		kind := args[0]
		if err := runMake(map[string]string{
			"KIND": kind,
		}, "gen", q); err == nil && !q {
			fmt.Println(kind)
		}
	},
}

var buildCmd = &cobra.Command{
	Use:   "build KIND",
	Short: "Build a digi image",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")

		kind := args[0]
		if err := runMake(map[string]string{
			"KIND": kind,
		}, "build", q); err == nil && !q {
			fmt.Println(kind)
		}
	},
}

var imageCmd = &cobra.Command{
	Use:   "image",
	Short: "List available digi images",
	Args:  cobra.ExactArgs(0),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")
		if !q {
			fmt.Println("IMAGE ID")
		}
		_ = runMake(nil, "list", q)
	},
}

// TBD pull and push to a remote repo
var pullCmd = &cobra.Command{
	Use:   "pull KIND",
	Short: "Pull a digi image",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")

		kind := args[0]
		if err := runMake(map[string]string{
			"KIND": kind,
		}, "pull", q); err != nil {
			return
		}

		if err := runMake(map[string]string{
			"KIND": kind,
		}, "build", true); err == nil && !q {
			fmt.Println(kind)
		}
	},
}

var pushCmd = &cobra.Command{
	Use:   "push KIND",
	Short: "Push a digi image",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")

		kind := args[0]
		if err := runMake(map[string]string{
			"KIND": kind,
		}, "push", q); err == nil && !q {
			fmt.Println(kind)
		}
	},
}

var logCmd = &cobra.Command{
	Use:     "log KIND",
	Short:   "Print log of a digi driver",
	Aliases: []string{"logs"},
	Args:    cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")

		name := args[0]
		if err := runMake(map[string]string{
			"NAME": name,
		}, "log", q); err == nil && !q {
		}
	},
}

var runCmd = &cobra.Command{
	Use:   "run KIND NAME",
	Short: "Run a digi given kind and name",
	Args:  cobra.ExactArgs(2),
	Run: func(cmd *cobra.Command, args []string) {
		var c string
		if l, _ := cmd.Flags().GetBool("local"); l {
			c = "test"
		} else {
			c = "run"
		}

		kopfLog := "false"
		if k, _ := cmd.Flags().GetBool("kopf-log"); k {
			kopfLog = "true"
		}

		createAlias := true
		if noAlias, _ := cmd.Flags().GetBool("no-alias"); noAlias {
			createAlias = false
		}

		quiet, _ := cmd.Flags().GetBool("quiet")
		kind, name := args[0], args[1]
		if err := runMake(map[string]string{
			"KIND":    kind,
			"NAME":    name,
			"KOPFLOG": kopfLog,
		}, c, quiet); err == nil && !quiet {
			fmt.Println(name)

			// add alias
			if createAlias {
				var workDir string
				if workDir = os.Getenv("WORKDIR"); workDir == "" {
					workDir = "."
				}

				type gvr struct {
					Group   string `yaml:"group,omitempty"`
					Version string `yaml:"version,omitempty"`
					Kind    string `yaml:"kind,omitempty"`
				}

				raw := gvr{}
				modelFile, err := ioutil.ReadFile(filepath.Join(workDir, kind, "model.yaml"))
				if err != nil {
					log.Printf("unable to create alias, cannot open model file: %v", err)
				}

				err = yaml.Unmarshal(modelFile, &raw)
				if err != nil {
					log.Fatalf("unable to create alias, cannot unmarshal model file: %v", err)
				}

				auri := &core.Auri{
					Kind: core.Kind{
						Group:   raw.Group,
						Version: raw.Version,
						Name:    raw.Kind,
					},
					Name: name,
					// XXX use ns from cmdline option once added
					Namespace: "default",
				}
				alias := api.Alias{
					Name: name,
					Auri: auri,
				}

				if err := alias.Set(); err != nil {
					log.Fatalf("unable to create alias %v", err)
				}
			}
		}
	},
}

var stopCmd = &cobra.Command{
	Use:   "stop KIND NAME",
	Short: "Stop a digi given kind and name",
	Args:  cobra.ExactArgs(2),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")
		if err := runMake(map[string]string{
			"KIND": args[0],
			"NAME": args[1],
		}, "stop", q); err == nil && !q {
			fmt.Println(args[1])
		}
	},
}

var rmiCmd = &cobra.Command{
	Use:   "rmi KIND",
	Short: "Remove a digi image",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		q, _ := cmd.Flags().GetBool("quiet")
		if err := runMake(map[string]string{
			"KIND": args[0],
		}, "delete", q); err == nil && !q {
			fmt.Printf("%s removed\n", args[0])
		}
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
					fmt.Println(err)
					os.Exit(1)
				}
				os.Exit(0)
			}

			if len(args) == 1 {
				fmt.Println("args should be either none or 2")
				os.Exit(1)
			}

			// parse the auri
			auri, err := api.ParseAuri(args[0])
			if err != nil {
				fmt.Printf("unable to parse auri %s: %v\n", args[0], err)
				os.Exit(1)
			}

			a := &api.Alias{
				Auri: &auri,
				Name: args[1],
			}

			if err := a.Set(); err != nil {
				fmt.Println("unable to set alias: ", err)
				os.Exit(1)
			}
		},
	}
	aliasClearCmd = &cobra.Command{
		Use:   "clear",
		Short: "clear all aliases",
		Args:  cobra.ExactArgs(0),
		Run: func(cmd *cobra.Command, args []string) {
			if err := api.ClearAlias(); err != nil {
				fmt.Println("unable to clear alias: ", err)
				os.Exit(1)
			}
		},
	}
	aliasResolveCmd = &cobra.Command{
		Use:   "resolve ALIAS",
		Short: "resolve an alias",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			if err := api.ResolveFromLocal(args[0]); err != nil {
				fmt.Printf("unable to resolve alias %s: %v\n", args[0], err)
				os.Exit(1)
			}
		},
	}
)

func Execute() {
	RootCmd.CompletionOptions.DisableDefaultCmd = true

	RootCmd.AddCommand(initCmd)
	RootCmd.AddCommand(genCmd)
	RootCmd.AddCommand(buildCmd)

	RootCmd.AddCommand(pullCmd)
	RootCmd.AddCommand(pushCmd)
	RootCmd.AddCommand(imageCmd)
	RootCmd.AddCommand(rmiCmd)

	RootCmd.AddCommand(runCmd)
	runCmd.Flags().BoolP("local", "l", false, "Run driver in local console")
	runCmd.Flags().BoolP("skip-alias", "n", false, "Do not create alias to the model")
	runCmd.Flags().BoolP("show-kopf-log", "k", false, "Enable kopf logging")
	RootCmd.AddCommand(stopCmd)
	RootCmd.AddCommand(logCmd)
	// TBD dq space ...
	// RootCmd.AddCommand(mountCmd)
	// RootCmd.AddCommand(pipeCmd)
	// TBD dq kc ... forward command to kubectl

	RootCmd.AddCommand(aliasCmd)
	aliasCmd.AddCommand(aliasClearCmd)
	aliasCmd.AddCommand(aliasResolveCmd)

	RootCmd.PersistentFlags().BoolP("quiet", "q", false, "Hide output")
	if err := RootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
