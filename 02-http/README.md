# 2. HTTP
Previously we set up a socket where a TCP connection was established. Now we can build HTTP on top of that. 
We will start with the basics and build more into it as we go. This means we start with HTTP/1 and slowly add layers which address the shortcomings of the previous versions. 


## HTTP/1.1
- In HTTP/1 each request sets up a new TCP connection. The TCP handshakes adds overhead. (we will skip over this and go streaight to HTTP/1.1)
- In HTTP/1.1 you presist the TCP connection to remove the overhead but your requests are still handled sequentially.

The request and response have the same skeleton (start line → headers → blank line → body). Only the first line is shaped differently. 
All HTTP communication follows the following format:

```
<start-line>\r\n
<header>: <value>\r\n
<header>: <value>\r\n
\r\n
<optional body>
```

### Start line
<details><summary>This is always the first thing you send.</summary>

The request has exactly three parts, separated by single spaces: method, path and version

```
GET / HTTP/1.1
```

However the response is shaped differently: version, status code, phrase

```
HTTP/1.1 200 OK
```

The status number is grouped by its first digit:
- 2xx: success (200 OK is the standard "here's your stuff")
- 3xx: redirect ("go look somewhere else")
- 4xx: client's fault (404 Not Found, 400 Bad Request)
- 5xx: server's fault (500 Internal Server Error)
</details>


### Line break

<details><summary>This is just a convention that was taken from SFTP and SMTP. Similar to how CSV uses a delimiter, in HTTP you also use a delimiter which is two bytes</summary>

- Carriage Return (CR) - `\r`
- Line Feed (LF) - `\n`

```
GET / HTTP/1.1\r\n
```
</details>

### Headers
<details><summary>You now add one header per line as a key value pair. </summary>

The only header HTTP/1.1 requires is in the request and that is `Host` which tells the server which website you want: `Host: example.com\r\n`. 
Responses technically doesn't need any headers but because TCP is just a byte stream, the client needs to know where the body ends. If you send a body with no length information, the client has no idea when to stop reading. So in practice you must include one of these on any response with a body:

- Content-Length — the byte count of the body
- Transfer-Encoding: chunked — for when you don't know the length of the response. Chunked encoding lets you send the body in pieces and signal the end without ever stating a total size. The size counts only the data bytes in that chunk — not the \r\n markers around it. To signal "I'm done," you send a final chunk with size zero, followed by a blank line: `0\r\n\r\n`

Once you are finished with the headers, you need to send a line break again: `\r\n`.

**Request**
```
GET / HTTP/1.1\r\nHost: example.com\r\n\r\n
```

**Response**
```
HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 13\r\nHello, world!
```

To make it more human readable I will add a line break after each delimiter from now on. Example:

Request
```
GET /path?query=1 HTTP/1.1\r\n
Host: example.com\r\n
User-Agent: my-client\r\n
Accept: */*\r\n
\r\n
```

Response
```
HTTP/1.1 200 OK\r\n
Content-Type: text/plain\r\n
Content-Length: 13\r\n
\r\n
Hello, world!
```

</details>


## HTTP/2
HTTP/1.1 suffers from head-of-line blocking. On one connection, requests are handled one at a time in orde. To overcome this, HTTP/2 implements a few ideas:
- Multiplexing
- Streams
- Binary framing
- Header compression (HPACK)

Multiplexing is interleaving the requests and responses so that they don't block each other. This means that insted of sending all the information about one request/response, you split them up into little chunks and send them concurrently, quickly switching from one data stream to another as soon as they're available. 
Each request/response pair gets a numbered "stream" so interleaved data can be sorted back out and everything is broken into small typed frames that carry these streams. From my understanding this concept is similar to Python's concurrency and threading. If you have multiple files being sent, you don't have to wait for file 1 to be completed before dealing with file 2. You get a chunk of each and whichever is served first can be sent to the client first while waiting for the other files to come.

### Frames

Let's first make sure we understand these two concepts.

<details><summary>hexadecimal number system</summary>

Hex numbers can include numbers 0-9 and/or letters a-f. 
Simimlar to a deck of cards where Jack can be 11, Queen 12, and King 13; the hex numbers just continue from 9 onwards where a is 10, b is 11 and so on until f which is 15 . 
Next step is the number position. Similar to binary where each bit is a power of 2 ie 2, 4, 8, 16, 32, etc; in hex number system each position is a power of 16. 
So we have 1, 16, 256, 4096. As you can see we can fit much larger numbers in a much smaller positions. 

For example: 3F8 is  (3x256, F(15)x16, 8x1) which equals 1016.

**What's a nibble**
Each byte has 8 bits (holds up to 255). A nibble is half a byte (4 bits). The small nible (bits with values 1, 2, 4, 8) can count up to 15. Guess what else goes up to 15. The hex numbers! So we call each hex number a nibble. 
  
</details>

<details><summary>endianness</summary>

This is all about how you arrange your bytes. You can start with the most significant bytes making up the biggest numbers on the left (big-endian) or you can start with the smallest ones on the left (small-endian). 

For example: you have a 16bit number `1011111011011100` (48860 decimal). You can split these 16bits into two bytes. But how would you order them?

- `[10111110, 11011100]` (big-endian)
- `[11011100, 10111110]` (small-endian)

Another example, number 260 in hex is `0x0104`.
- `[0x01, 0x04]` (big-endian) 
- `[0x04, 0x01]` (small-endian)

Just know that HTTP/2 uses big-endian so the bytes are ordered from left to right from most significant to least significant. 

</details>

When talking about framing, forget about the content that will be included in the data frames and let's just discuss how we'd break up the data to send them over the network. Framing is on another level to the request itself and is more about how data is transferred. The HTTP request and response procedure doesn't change compared to the pervious version. 

Each Frame has a header (9 bytes) so that the receiver can identify which frame is for which request, how much data is included in that frame, etc. More specifically, the frame headers describe:
- Length (3 bytes): size of the payload that follows, not counting these 9 header bytes.
- Type (1 byte): what kind of frame. 0x0 = DATA, 0x1 = HEADERS, 0x4 = SETTINGS.
- Flags (1 byte): A bitfield flag that tells us whether the stream has ended or starting etc (END_STREAM = 0x1, END_HEADERS = 0x4).
- Stream ID (4 bytes): which stream. Note: the top bit of these 4 bytes is reserved and must be 0, so it's really 31 bits.

```
Byte:  0    1    2    3      4      5    6    7    8
      [   Length    ][ Type ][Flags][   Stream ID     ]
       └─ 3 bytes ─┘  1 byte  1 byte └─── 4 bytes ────┘
```

That's all there is to it really. You look at the data you want to send over, attach the metadata in the format agreed above, and then concatenate the metadata (header) to the payload and send it across. On the other side you reverse engineer it and read the data. 

<details><summary>Frame types and flags</summary>

**Frame types**

| Type | Value | Purpose |
|------|-------|---------|
| DATA | 0x0 | Carries message body bytes |
| HEADERS | 0x1 | Carries HPACK-compressed headers (opens a stream) |
| PRIORITY | 0x2 | Stream priority hints (deprecated in practice) |
| RST_STREAM | 0x3 | Abruptly terminate one stream |
| SETTINGS | 0x4 | Connection configuration exchange |
| PUSH_PROMISE | 0x5 | Server push (largely deprecated) |
| PING | 0x6 | Keepalive / round-trip measurement |
| GOAWAY | 0x7 | Shut down the whole connection gracefully |
| WINDOW_UPDATE | 0x8 | Flow control credit |
| CONTINUATION | 0x9 | Overflow for header blocks too big for one HEADERS frame |

**HEADERS frame flags**

| Flag | Bit | Meaning |
|------|-----|---------|
| END_STREAM | 0x1 | No more frames from this side on this stream (e.g. a GET with no body) |
| END_HEADERS | 0x4 | The header block is complete — no CONTINUATION frames follow |
| PADDED | 0x8 | The payload includes padding bytes |
| PRIORITY | 0x20 | The payload includes priority info |

**DATA frame flags**

| Flag | Bit | Meaning |
|------|-----|---------|
| END_STREAM | 0x1 | This is the last body frame on this stream |
| PADDED | 0x8 | The payload includes padding bytes |

**SETTINGS frame flags**

| Flag | Bit | Meaning |
|------|-----|---------|
| ACK | 0x1 | Acknowledgement of the peer's SETTINGS (payload must be empty) |

**PING frame flags**

| Flag | Bit | Meaning |
|------|-----|---------|
| ACK | 0x1 | This PING is a reply to a received PING |

**PUSH_PROMISE frame flags**

| Flag | Bit | Meaning |
|------|-----|---------|
| END_HEADERS | 0x4 | Header block complete |
| PADDED | 0x8 | Payload includes padding |

**CONTINUATION frame flags**

| Flag | Bit | Meaning |
|------|-----|---------|
| END_HEADERS | 0x4 | The header block is now complete |

**Frame types with no flags**

RST_STREAM, GOAWAY, WINDOW_UPDATE, and PRIORITY define no flags — their Flags byte is always 0x00.

</details>

### Streams
Stream IDs have rules:
- Client-initiated streams use odd IDs (1, 3, 5, 7…). Server-initiated (push) streams use even IDs. So a client counts up by 2 for each new request.
- IDs only increase — you never reuse a stream ID on a connection. Once stream 3 is done, its number is retired.
- Stream 0 is reserved for connection-level control frames (things that affect the whole connection, not one request).

Example:
1. Client sends a HEADERS frame on stream 1
2. If there's a request body, client sends DATA frames on stream 1
3. Server sends a HEADERS frame on stream 1
4. Server sends DATA frames on stream 1
5. A flag called END_STREAM marks the last frame in each direction; once both sides have sent it, stream 1 is closed.
All of this can be happening for streams 3, 5, and 7 simultaneously, their frames interleaved on the wire.

#### END_STREAM
END_STREAM says: "this is the last frame I'm sending on this stream".
Each direction sends its own END_STREAM. When both the client and the server have sent one, the stream is fully closed and its ID is retired.

- On a HEADERS frame → "these are my headers, and I have no body — I'm done." (Exactly the case for a GET request: one HEADERS frame with END_STREAM set, no DATA frames.)
- On a DATA frame → "this is the final piece of the body — I'm done sending data."

A GET request (no body) — a single HEADERS frame with END_STREAM set:

```
Length:    (size of compressed headers)
Type:      0x1   (HEADERS)
Flags:     0x05  ← see note below
Stream ID: 1
```

Note that the flag is set to 0x05 and not 0x01. This is because a HEADERS frame usually also sets END_HEADERS (bit 0x4, meaning "the header block is complete"). 0x01 (END_STREAM) + 0x04 (END_HEADERS) combine to 0x05. This is the bitfield in action — multiple flags packed into the one byte by OR-ing their bit values together.

### HPACK-compression
In HTTP/1.1, headers are plain text sent in full every single time. Now the client requests /page2, /page3, /page4. Almost every header is identical each time — same Host, same User-Agent, same Cookie. You're re-sending the same hundreds of bytes over and over. On a page with 100 requests, that's enormously wasteful.
HPACK's job: don't send the same header text repeatedly. Send it once, then refer back to it with a tiny reference.

1. The static table
HPACK ships with a fixed, built-in table of 61 common headers that both client and server already know — no need to transmit it. A small sample:

```
Index  Header name        Value
1      :authority         (empty)
2      :method            GET
3      :method            POST
4      :path              /
8      :status            200
...
```

So instead of sending the bytes for :method: GET, you send the single number 2. The receiver looks up index 2 in its static table and knows it means :method: GET. Hundreds of bytes collapse to one.

2. The dynamic table
The static table only covers common headers. What about your specific ones, like Cookie: session=abc123 or a custom User-Agent?
The dynamic table handles these. It starts empty and both sides build it up as the connection runs:

The first time you send User-Agent: Mozilla/5.0..., you send it in full — but you also add it to the dynamic table.
The receiver, seeing it, adds it to its dynamic table too.
Next time you need that same header, you just send its index number.

The dynamic table entries get appended after the static ones (so they start at index 62). Both sides append in the same order, so their tables stay identical. This is the crucial and hard part: both sides must keep their dynamic tables perfectly synchronized. Every header you add on the sending side, the receiver must add in the exact same order. If they ever disagree — if one side adds an entry the other didn't, or in a different order — every index reference after that point resolves to the wrong header, and the connection is corrupted beyond recovery. 

3. Huffman coding
For header text that does have to be sent literally (a value never seen before), HPACK optionally compresses the string itself with Huffman coding — a scheme that represents common characters with fewer bits. A single flag bit on each string says whether it's Huffman-encoded or raw. This shrinks the literal strings further. (watch a yt video to understand this part)

**Why not just use gzip?**
Reasonable question — gzip compresses repetitive text well. The answer is security. A famous attack called CRIME showed that if you gzip-compress data that mixes secret values (like a session cookie) with attacker-influenced values, the compressed size leaks information about the secret. HPACK was designed specifically to compress headers without that vulnerability. So it's a purpose-built format, not general-purpose compression.



## HTTP/3
HTTP/2 removes head-of-line blocking at the HTTP layer so no request blocks another. But all these streams still ride on a single TCP connection, and TCP itself delivers bytes strictly in order. If a TCP packet is lost, TCP holds back all the data behind it until the lost packet is retransmitted — which stalls every stream at once.
So HTTP/2 moved the blocking problem down a layer rather than fully eliminating it. This is precisely why HTTP/3 exists: it replaces TCP with QUIC (built on UDP) so that a lost packet only stalls its own stream, not all of them.

This is pretty huge so I'm gonna park this until I do all of the above and if I still haven't learned enough we'll go for HTTP/3



# How to run 
Starting the server:

```
go run server.go
```

Once you start the client you have to manually write the request

```
go run client.go
GET /helloworld HTTP/1.1\r\n\r\n
```

What I've done so far:
- establish a TCP soc and listen (both server and client)
- client to take user input and replace escaped chars to send bytes to server
- server receives bytes and parses the HTTP request
      - then it routes it to the respective handler with the request
      - the endpoint handles the request and writes a response
      - in between we also write error responses if something goes wrong
- client gets response back and writes it to console


I learned a lot about reader/writer interfaces but I'm not really interested in parsing bytes so I'll leave this here. I'll use the info in my other project to set up a server and build my API