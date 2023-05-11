package net

import (
	"os"
	"os/exec"
	"strconv"

	"digi.dev/digi/api/k8s"
	"github.com/spf13/cobra"

	// kubernetes go library
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/kubernetes/scheme"
	"k8s.io/client-go/tools/clientcmd"
	"k8s.io/client-go/tools/remotecommand"
)

var RootCmd = &cobra.Command{
	Use:   "net [command]",
	Short: "Manage the dNet",
}

var PingCmd = &cobra.Command{
	Use:     "ping TARGET [SRC]",
	Short:   "Ping a digi, from local device or from another digi",
	Aliases: []string{"p"},
	Args:    cobra.MinimumNArgs(1),
	Run: func(cmd *cobra.Command, args []string) {

		target := args[0]
		duration, _ := cmd.Flags().GetInt("duration")

		if len(args) == 1 {
			// ping from local device

			// TODO: digi connect target 8534

			// create the command
			command := []string{
				"hping3",
				"-S",
				"localhost",
				"-p",
				"8534",
				"-c",
				strconv.Itoa(duration),
			}

			// execute the command
			execCmd := exec.Command(command[0], command[1:]...)
			execCmd.Stdout = os.Stdout
			execCmd.Stderr = os.Stderr
			execCmd.Stdin = os.Stdin
			if err := execCmd.Run(); err != nil {
				print(err)
			}

			// TODO: tear down digi connect target 8534

		} else {
			// ping from another digi

			source := args[1]

			// use the current context in kubeconfig
			config, err := clientcmd.BuildConfigFromFlags("", k8s.KubeConfigFile())
			if err != nil {
				panic(err.Error())
			}

			// create the clientset
			clientset, err := kubernetes.NewForConfig(config)
			if err != nil {
				panic(err.Error())
			}

			// create the command
			command := []string{
				"hping3",
				"-S",
				target,
				"-p",
				"8534",
				"-c",
				strconv.Itoa(duration),
			}

			// get pod name from label
			podList, err := clientset.CoreV1().Pods("default").List(cmd.Context(), metav1.ListOptions{
				LabelSelector: "name=" + source,
				FieldSelector: "status.phase=Running",
			})
			if err != nil {
				panic(err.Error())
			}
			if len(podList.Items) == 0 {
				panic("source pod not found: " + source)
			}

			// get the first pod
			pod := podList.Items[0]

			// execute the command
			req := clientset.CoreV1().RESTClient().Post().
				Resource("pods").
				Name(pod.Name).
				Namespace("default").
				SubResource("exec").
				VersionedParams(&corev1.PodExecOptions{
					Command:   command,
					Container: "probe",
					Stdin:     true,
					Stdout:    true,
					Stderr:    true,
					TTY:       true,
				}, scheme.ParameterCodec)

			exec, err := remotecommand.NewSPDYExecutor(config, "POST", req.URL())
			if err != nil {
				panic(err)
			}
			err = exec.Stream(remotecommand.StreamOptions{
				Stdin:  os.Stdin,
				Stdout: os.Stdout,
				Stderr: os.Stderr,
				Tty:    true,
			})
			if err != nil {
				panic(err)
			}
		}
	},
}

func init() {
	RootCmd.AddCommand(PingCmd)

	PingCmd.Flags().IntP("duration", "d", 10, "Number of packets to send.")
}
