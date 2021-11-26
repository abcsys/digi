package helper

import (
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"

	"github.com/creack/pty"
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

	ptmx, err := pty.Start(cmd_)
	if err != nil {
		panic(err)
	}
	defer func() { _ = ptmx.Close() }()

	_, err = io.Copy(os.Stdout, ptmx)
	if err != nil {
		panic(err)
	}

	// TBD streaming output
	return nil
}
