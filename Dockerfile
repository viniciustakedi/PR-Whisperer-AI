FROM golang:1.24

WORKDIR /github/workspace

RUN go build -o main

ENTRYPOINT ["/github/workspace/main"]