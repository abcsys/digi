package main

import (
	"fmt"
	"net/http"
)

func handler(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintf(w, "Response!")
}

// TO COMPILE FOR BUSYBOX:
// GOOS=linux GOARCH=amd64 go build server.go

func main() {
	http.HandleFunc("/", handler)
	// fmt.Println("Server running...")
	http.ListenAndServe(":8534", nil)
}
