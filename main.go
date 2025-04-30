package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"os/exec"
	"strings"

	openai "github.com/sashabaranov/go-openai"
)

func main() {
	apiKey := os.Getenv("INPUT_OPENAI_API_KEY")
	if apiKey == "" {
		log.Fatal("Missing OPENAI_API_KEY env.")
	}

	diff := runCmd("git", "diff", "origin/main...HEAD")
	commitMsg := runCmd("git", "log", "--pretty=%B")

	client := openai.NewClient(apiKey)

	prompt := fmt.Sprintf(`
	Generate a PR description.
	Commit message: %s
	Diff: %s
	`, commitMsg, diff)

	resp, err := client.CreateChatCompletion(context.Background(), openai.ChatCompletionRequest{
		Model: openai.GPT4o,
		Messages: []openai.ChatCompletionMessage{
			{Role: "user", Content: prompt},
		},
	})
	if err != nil {
		log.Fatal(err)
	}

	desc := resp.Choices[0].Message.Content
	fmt.Println("::set-output name=description::" + strings.ReplaceAll(desc, "\n", "\\n"))
}

func runCmd(name string, args ...string) string {
	out, err := exec.Command(name, args...).CombinedOutput()
	if err != nil {
		log.Fatalf("Error running %s %v: %v\nOutput:\n%s", name, args, err, string(out))
	}

	return string(out)
}
