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
	apiKey := os.Getenv("INPUT_OPENAI_API_KEY")
	if apiKey == "" {
		log.Fatal("OpenAI API key is empty")
	}

	runCmd("git", "config", "--global", "--add", "safe.directory", "/github/workspace")

	client := openai.NewClient(apiKey)

	baseRef := os.Getenv("GITHUB_BASE_REF")
	if baseRef == "" {
		log.Fatal("GITHUB_BASE_REF is not set")
	}

	fmt.Println("🔍 Base branch:", baseRef)

	runCmd("git", "fetch", "origin", baseRef)
	base := runCmd("git", "merge-base", "HEAD", "origin/"+baseRef)
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
