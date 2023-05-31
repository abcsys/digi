package config

import (
	"fmt"
	"os"
	"os/user"
	"path/filepath"
	"strings"

	"github.com/spf13/viper"

	"digi.dev/digi/api/helper"
)

var (
	configDir string
)

func init() {
	usr, err := user.Current()
	if err != nil {
		panic(err)
	}

	configDir = filepath.Join(usr.HomeDir, ".digi")
	if err := helper.EnsureDir(configDir); os.IsNotExist(err) {
		panic(err)
	}

	Load()
}

func Load() {
	viper.SetConfigName("config")
	viper.SetConfigType("yaml")
	viper.AddConfigPath(configDir)

	if err := viper.ReadInConfig(); err != nil {
		if _, ok := err.(viper.ConfigFileNotFoundError); ok {
			fileName := filepath.Join(configDir, "config")

			helper.Touch(fileName)
			fmt.Printf("digi: new config file at: %s; try again\n", fileName)
		} else {
			panic(fmt.Errorf("Fatal error config file: %s \n", err))
		}
	}
}

func Get(key string) (string, error) {
	configs := make(map[string]string)
	if err := viper.UnmarshalKey("config", &configs); err != nil {
		return "", err
	}
	// XXX ToLower() a hack to get around the fact that viper doesn't
	// support upper case keys
	config, ok := configs[strings.ToLower(key)]
	if !ok {
		return "", fmt.Errorf("config %s not found", key)
	}

	return config, nil
}

func Set(key, value string) error {
	configs := make(map[string]string)
	if err := viper.UnmarshalKey("config", &configs); err != nil {
		return err
	}
	configs[strings.ToLower(key)] = value

	viper.Set("config", configs)
	return viper.WriteConfig()
}

func ShowAll() error {
	configs := make(map[string]string)
	if err := viper.UnmarshalKey("config", &configs); err != nil {
		return err
	}

	for k, v := range configs {
		fmt.Println(k, ":", v)
	}
	return nil
}

func ClearConfig() error {
	configs := make(map[string]string)
	viper.Set("config", configs)
	return viper.WriteConfig()
}
