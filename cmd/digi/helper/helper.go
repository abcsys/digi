package helper

import (
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"net"
	"os"
	"os/exec"
	"os/signal"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"syscall"

	"digi.dev/digi/api"
	"digi.dev/digi/pkg/core"
	"github.com/creack/pty"
	"golang.org/x/term"
	"gopkg.in/yaml.v2"
)

var homeDir string

func init() {
	var err error
	homeDir, err = os.UserHomeDir()
	if err != nil {
		log.Fatalf("unable to find home dir: %v\n", err)
	}
	homeDir = filepath.Join(homeDir, ".digi")
}

func RunMake(args map[string]string, cmd string, usePtx, quiet bool) error {
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
			log.Fatalf("unable to find work dir: %v\n", err)
		}
		cmd_.Env = append(cmd_.Env,
			fmt.Sprintf("WORKDIR=%s", curDir),
		)
	}
	cmd_.Dir = homeDir

	if !usePtx || quiet {
		if !quiet {
			output, _ := cmd_.Output()
			fmt.Print(string(output))
		} else {
			_ = cmd_.Run()
		}
		return nil
	}

	// TBD use k8s.io/kubectl/pkg/util/term
	ptmx, err := pty.Start(cmd_)
	if err != nil {
		panic(err)
	}
	defer func() { _ = ptmx.Close() }()

	// Start a shell session: github.com/creack/pty
	// Handle pty size.
	ch := make(chan os.Signal, 1)
	signal.Notify(ch, syscall.SIGWINCH)
	go func() {
		for range ch {
			if err := pty.InheritSize(os.Stdin, ptmx); err != nil {
				log.Printf("error resizing pty: %s", err)
			}
		}
	}()
	ch <- syscall.SIGWINCH                        // Initial resize.
	defer func() { signal.Stop(ch); close(ch) }() // Cleanup signals when done.

	// Set stdin in raw mode.
	oldState, err := term.MakeRaw(int(os.Stdin.Fd()))
	if err != nil {
		panic(err)
	}
	defer func() { _ = term.Restore(int(os.Stdin.Fd()), oldState) }() // Best effort.

	// Copy stdin to the pty and the pty to stdout.
	// NOTE: The goroutine will keep reading until the next keystroke before returning.
	go func() { _, _ = io.Copy(ptmx, os.Stdin) }()

	_, _ = io.Copy(os.Stdout, ptmx)

	return nil
}

func GetKindFromProfile(dirName string) (*core.Kind, error) {
	var workDir string
	if workDir = os.Getenv("WORKDIR"); workDir == "" {
		workDir = "."
	}

	// TBD add struct tags for yaml to core.Kind and core.Auri
	raw := struct {
		Group   string `yaml:"group,omitempty"`
		Version string `yaml:"version,omitempty"`
		Kind    string `yaml:"kind,omitempty"`
	}{}

	modelFile, err := ioutil.ReadFile(filepath.Join(workDir, dirName, "model.yaml"))
	if err != nil {
		// TBD report profile missing
		return nil, fmt.Errorf("cannot open model file: %v", err)
	}

	err = yaml.Unmarshal(modelFile, &raw)
	if err != nil {
		return nil, fmt.Errorf("cannot unmarshal model file: %v", err)
	}

	return &core.Kind{
		Group:   strings.ToLower(raw.Group),
		Version: strings.ToLower(raw.Version),
		Name:    strings.ToLower(raw.Kind),
	}, nil
}

func CreateAlias(kind *core.Kind, name, namespace string) error {
	auri := &core.Auri{
		Kind:      *kind,
		Name:      name,
		Namespace: namespace,
	}
	alias := api.Alias{
		Name: name,
		Duri: auri,
	}

	if err := alias.Set(); err != nil {
		return fmt.Errorf("unable to create alias: %v", err)
	}
	return nil
}

func GetPort() int {
	addr, err := net.ResolveTCPAddr("tcp", "localhost:0")
	if err != nil {
		log.Fatalf("unable to get port: %v\n", err)
	}

	l, err := net.ListenTCP("tcp", addr)
	if err != nil {
		log.Fatalf("unable to get port: %v\n", err)
	}
	_ = l.Close()
	return l.Addr().(*net.TCPAddr).Port
}

// checks if the string includes a range
func isExpandSyntax(arg string) bool {
	re := regexp.MustCompile(`\{\d{1,}..\d{1,}\}`)
	return re.FindString(arg) != ""
}

func ExpandArgs(args []string) []string {
	var res []string
	re := regexp.MustCompile(`(.*)\{(\d{1,})..(\d{1,})\}(.*)`)
	for _, arg := range args {
		if isExpandSyntax(arg) {
			matches := re.FindStringSubmatch(arg)
			if len(matches) == 5 {
				prefix, start_str, end_str, suffix := matches[1], matches[2], matches[3], matches[4]

				start, e := strconv.Atoi(start_str)
				if e != nil {
					panic(e)
				}
				end, e := strconv.Atoi(end_str)
				if e != nil {
					panic(e)
				}

				expanded_prefixes := ExpandArgs([]string{prefix})
				for _, expanded_prefix := range expanded_prefixes {
					for i := start; i <= end; i++ {
						res = append(res, fmt.Sprintf("%s%d%s", expanded_prefix, i, suffix))
					}
				}
			} else {
				res = append(res, arg)
			}
		} else {
			res = append(res, arg)
		}
	}
	return res
}
