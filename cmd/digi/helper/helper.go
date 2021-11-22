package helper

import (
	"bytes"
	"fmt"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

var homeDir string

func init() {
	var err error
	homeDir, err = os.UserHomeDir()
	if err != nil {
		panic(err)
	}
	homeDir = filepath.Join(homeDir, ".digi")
}

func RunMake(args map[string]string, cmd string, quiet bool) error {
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

	// TBD fix output string
	// TBD invoked detached shell
	// TBD streaming output
	return nil
}
