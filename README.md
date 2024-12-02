# YouTube Video Summarizer

![11](https://github.com/user-attachments/assets/6c29ba43-c35d-4a9a-be91-e2627414e320)

## Prerequisites

Before using this application, you need to:

1. Install Ollama

   - Windows: Download from https://ollama.ai/download/windows
   - macOS: Download from https://ollama.ai/download/mac
   - Linux: Download from https://ollama.ai/download/linux

2. Install LLM Model
   After installing Ollama, open terminal and run:

   ```bash
      ollama pull llama3.2
   ```

> **Note:**
>
> - Currently, only llama3.2 model is supported.

## Installation

1. Install the application

   ```bash
      python -m venv venv
      source venv/bin/activate
      pip install -r requirements.txt
   ```

2. Run the application

   ```bash
      python src/video_summary/app.py
   ```

## TODO

- [ ] Add more LLM models
- [ ] Add more UI
- [ ] Add more features

## Troubleshooting

If you encounter any issues:

1. Make sure Ollama is running
2. Verify llama3.2 model is installed
3. Restart the application
