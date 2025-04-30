FROM golang:1.24

WORKDIR /app

COPY . .

RUN go build -o main

ENTRYPOINT [ "/app/main" ]