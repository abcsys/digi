package main

import (
	"fmt"
	"os"

	"digi.dev/digi/cmd/digi/digi"
)

func main() {
	// natural language interface
	if err := digi.ChatCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
