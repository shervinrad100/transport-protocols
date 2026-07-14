package main

import (
	"bufio"
	"context"
	"fmt"
	"io"
	"log"
	"net"
	"os"
	"strings"
	"time"
)

func sendRequest(conn net.Conn) error {
	var escaper = strings.NewReplacer(
		`\r`, "\r",
		`\n`, "\n",
		`\t`, "\t",
		`\\`, "\\",
	)

	// continuously read from stdin and write everything into the connection
	reader := bufio.NewReader(os.Stdin)
	line, err := reader.ReadString('\n')
	if err != nil {
		log.Fatal(err)
	}
	line = strings.TrimRight(line, "\r\n")
	unescaped := escaper.Replace(line)
	if _, err := conn.Write([]byte(unescaped)); err != nil {
		log.Fatal(err)
		return err
	}

	resp, err := io.ReadAll(conn)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println(string(resp))

	return nil
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

	sendRequest(conn)
}
