package main

import (
	"log"

	"digi.dev/digi/cmd/digi/digi"
)

func main() {
	if err := digi.RootCmd.Execute(); err != nil {
		log.Fatalln(err)
	}
}
