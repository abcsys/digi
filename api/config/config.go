package config

import (
	"fmt"
	"os"
	"os/user"
	"path/filepath"

	"github.com/spf13/viper"
)

var (
	configDir string
)

func init() {
	usr, err := user.Current()
	if err != nil {
		panic(err)
	}

	configDir = filepath.Join(usr.HomeDir, ".dq")
	if err := ensureDir(configDir); os.IsNotExist(err) {
		panic(err)
	}
}

func Load() {
	viper.SetConfigName("config")
	viper.SetConfigType("yaml")
	viper.AddConfigPath(configDir)

	if err := viper.ReadInConfig(); err != nil {
		if _, ok := err.(viper.ConfigFileNotFoundError); ok {
			fileName := filepath.Join(configDir, "config")

			touch(fileName)
			fmt.Println("dq: new config file at: ", fileName)
			fmt.Println("dq: try again")
		} else {
			panic(fmt.Errorf("Fatal error config file: %s \n", err))
		}
	}
}

func touch(name string) {
	_, err := os.OpenFile(name, os.O_RDONLY|os.O_CREATE, 0644)
	if err != nil {
		panic(err)
	}
}

func ensureDir(name string) error {
	if _, err := os.Stat(name); os.IsNotExist(err) {
		return os.MkdirAll(configDir, 0700)
	}
	return nil
}
