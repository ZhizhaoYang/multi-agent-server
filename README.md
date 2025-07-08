# Multi-Agent Server

A multi-agent AI system built with LangGraph for orchestrating intelligent conversations.

## Features

- Multi-department agent workflow
- Real-time streaming responses
- PostgreSQL/SQLite checkpointing
- FastAPI web interface
- Thought chain processing

## Quick Start

```bash
# Install dependencies
uv pip install -e .

# Run the server
make run
```

## API

- `POST /chat-stream` - Send messages to the AI system
- `DELETE /clear-history` - Clear all conversation history from SQLite database