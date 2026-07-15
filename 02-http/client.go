package main

import (
	"bufio"
	"context"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"os"
	"strings"
	"time"
)

func runClient(conn net.Conn) error {
	var escaper = strings.NewReplacer(
		`\r`, "\r",
		`\n`, "\n",
		`\t`, "\t",
		`\\`, "\\",
	)

	// continuously read from stdin and write everything into the connection
	stdin := bufio.NewReader(os.Stdin)
	responseReader := bufio.NewReader(conn)

	for {
		fmt.Print("> ")
		line, err := stdin.ReadString('\n')
		if err != nil {
			if err == io.EOF {
				return nil
			}
			return err
		}
		line = strings.TrimRight(line, "\r\n")
		if line == "" {
			continue
		}

		// send one request
		if _, err := conn.Write([]byte(escaper.Replace(line))); err != nil {
			return err
		}

		// Read one response
		resp, err := http.ReadResponse(responseReader, nil)
		if err != nil {
			return err
		}
		body, _ := io.ReadAll(resp.Body)
		fmt.Println(resp.Status, "\n"+string(body))
		resp.Body.Close()
	}

}

func main() {
	// Create the client with a timeout context
	var dialer net.Dialer
	ctx, cancel := context.WithTimeout(context.Background(), time.Minute*10)
	defer cancel()

	conn, err := dialer.DialContext(ctx, "tcp", "127.0.0.1:5001")
	if err != nil {
		log.Fatal(err)
	} else {
		fmt.Println("Connected to", conn.RemoteAddr())
	}
	defer conn.Close()

	runClient(conn)
}
