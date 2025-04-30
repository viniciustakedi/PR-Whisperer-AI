package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"os/exec"

	openai "github.com/sashabaranov/go-openai"
)

func main() {
	if len(os.Args) < 2 {
		log.Fatal("Missing OpenAI API key as argument.")
	}
	apiKey := os.Args[1]

	client := openai.NewClient(apiKey)

	// Get git diff
	base := runCmd("git", "merge-base", "HEAD", "origin/main")
	diff := runCmd("git", "diff", base, "HEAD")
	commitMsg := runCmd("git", "log", "-1", "--pretty=%B")

	// Prompt to send to OpenAI
	prompt := fmt.Sprintf(`Generate a clear and professional PR description.
Commit message: %s
Code diff: %s`, commitMsg, diff)

	// Make the API call
	resp, err := client.CreateChatCompletion(context.Background(), openai.ChatCompletionRequest{
		Model: openai.GPT4,
		Messages: []openai.ChatCompletionMessage{
			{Role: "user", Content: prompt},
		},
	})
	if err != nil {
		log.Fatalf("OpenAI API error: %v", err)
	}

	result := resp.Choices[0].Message.Content
	fmt.Println("🔍 AI-Generated PR Description:")
	fmt.Println(result)
}

func runCmd(name string, args ...string) string {
	out, err := exec.Command(name, args...).CombinedOutput()
	if err != nil {
		log.Fatalf("Error running %s %v:\n%s", name, args, out)
	}
	return string(out)
}
