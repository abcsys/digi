package helper

import (
	"os"
)

func Touch(name string) {
	_, err := os.OpenFile(name, os.O_RDONLY|os.O_CREATE, 0644)
	if err != nil {
		panic(err)
	}
}

func EnsureDir(name string) error {
	if _, err := os.Stat(name); os.IsNotExist(err) {
		return os.MkdirAll(name, 0700)
	}
	return nil
}
