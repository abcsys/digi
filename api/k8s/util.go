package k8s

import (
	"fmt"
	"io/ioutil"
	"log"
	"net"
	"net/url"
	"os"
	"path/filepath"
)

func PathExists(path string) (bool, error) {
	if _, err := os.Stat(path); err == nil {
		return true, nil
	} else if os.IsNotExist(err) {
		return false, nil
	} else {
		return false, fmt.Errorf("unknown file status: %v", err)
	}
}

func ValidURL(s string) bool {
	if _, err := url.ParseRequestURI(s); err != nil {
		return false
	} else {
		return true
	}
}

func ValidIP(s string) bool {
	if ip := net.ParseIP(s); ip == nil {
		return false
	} else {
		return true
	}
}

func DeleteFiles(files ...string) error {
	succeed := true

	for _, f := range files {
		if err := os.Remove(f); err != nil {
			succeed = false
		}
	}

	if !succeed {
		return fmt.Errorf("some files cannot be removed, check log for details")
	}
	return nil
}

func PrintFile(file string) {
	content, err := ioutil.ReadFile(file)
	if err != nil {
		log.Fatal(err)
	}

	fmt.Println(string(content))
}

func createFileIfNotExist(file string) error {
	if err := os.MkdirAll(filepath.Dir(file), 0777); err != nil {
		return fmt.Errorf("unable to create directory for file %s: %v", file, err)
	}

	f, err := os.OpenFile(file, os.O_RDONLY|os.O_CREATE, 0666)
	if err != nil {
		return fmt.Errorf("unable to create file %s: %v", file, err)
	}
	return f.Close()
}
