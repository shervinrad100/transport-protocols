package main

import (
	"bufio"
	"errors"
	"flag"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"time"
)

const HTTP_PROTO = "HTTP/1.0"

type httpHandler func(conn net.Conn, req *http.Request)

var routes = map[string]httpHandler{
	"/helloworld": helloWorld,
}

func helloWorld(conn net.Conn, req *http.Request) {
	if req.Method != http.MethodGet {
		writeResponse(conn, 501, "Not Implemented", "")
	}
	writeResponse(conn, 200, "OK", "Hello World!")
}

func handleConnection(conn net.Conn) {
	// cleanup connection
	defer conn.Close()
	conn.SetDeadline(time.Now().Add(5 * time.Minute))

	// Connect reader to connection
	reader := bufio.NewReader(conn)

	// Read the request
	request, err := http.ReadRequest(reader)
	if err != nil {
		log.Println(err)
		// writeResponse(conn, 500, "Internal Server Error", "")
		return
	}

	// Read body
	if request.ContentLength > 0 {
		const maxBody = 1 << 20
		var body []byte
		defer request.Body.Close()

		if request.ContentLength > 0 {
			if request.ContentLength > maxBody {
				writeResponse(conn, 413, "Content Too Large", "")
			}
			body = make([]byte, request.ContentLength)
			n, err := io.ReadFull(request.Body, body)
			if err != nil {
				log.Println(err)
				if errors.Is(err, io.ErrUnexpectedEOF) {
					writeResponse(conn, 400, "Bad Request", "Request body was truncated or incomplete.")
				} else {
					writeResponse(conn, 500, "Internal Server Error", "")
				}
			}
			log.Println("read %i bytes", n)
		} else {
			body, err = io.ReadAll(io.LimitReader(request.Body, maxBody))
		}
	}

	// pass to relevant endpoint
	handler, ok := routes[request.URL.Path]
	if ok {
		handler(conn, request)
	} else {
		writeResponse(conn, 404, "Not Found", "")
	}

}

func writeResponse(conn net.Conn, statusCode int, status, body string) error {
	// HTTP/1.1 <code> <reason>\r\n<body>\r\n\r\n
	response := fmt.Sprintf("%s %d %s\r\nContent-Length: %d\r\n%s\r\n\r\n", HTTP_PROTO, statusCode, status, len(body), body)
	_, err := conn.Write([]byte(response))
	fmt.Println("Responding to", conn.RemoteAddr(), response)
	return err
}

func main() {

	// Take server details from user input
	IP := flag.String("ip", "127.0.0.1", "Server IP")
	PORT := flag.String("port", "5001", "Server port")
	flag.Parse()

	// Set up a TCP server
	listener, err := net.Listen("tcp", *IP+":"+*PORT)
	if err != nil {
		log.Fatal(err)
	}
	defer listener.Close()

	// Main loop keeping server alive - receive requests
	log.Println("Listening for connections...")
	for {
		// Wait for a connection.
		conn, err := listener.Accept()
		if err != nil {
			log.Println(err)
			writeResponse(conn, 500, "Internal Server Error", "")
		} else {
			log.Println(conn.RemoteAddr(), "has connected.")
		}

		// connection handled in go routine
		go handleConnection(conn)

	}
}
