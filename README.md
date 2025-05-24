# Multi-Agent Server with SSE Streaming

A server application for managing multiple AI agents that collaborate to complete tasks, featuring real-time streaming responses with Server-Sent Events (SSE).

## Features

- **Multi-Agent Orchestration**: Coordinated interaction between specialized agents (Researcher, Map Searcher, General Response)
- **Real-time Streaming**: Server-Sent Events (SSE) for incremental result delivery
- **Graceful Streaming**: Stream response chunks as they're generated, not after completion
- **Node Visibility**: Transparency into which agent is currently processing your request
- **Streaming Modes**: Support for both "messages" and "updates" streaming formats
- **Error Handling**: Robust error handling throughout the streaming process
- **Incremental Content Delivery**: Using AIMessageChunk for optimized token delivery

## Setup

```bash
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

## Environment Variables

Create a `.env` file in the root directory with:

```
DEEPSEEK_API_KEY=your_deepseek_api_key
GAODE_SSE_URL=https://mcp.amap.com/sse?key=your_gaode_map_key
```

## Running the Streaming Demo

The repository includes a demonstration of streaming capabilities:

```bash
# Run the streaming demo
make demo-streaming
# or
python -m main
```

## Running the API Server

To start the FastAPI server with streaming endpoints:

```bash
# Start development server
make run
# or
uvicorn app.main:app --reload --port 8000 --log-level debug
```

## API Endpoints

### Streaming Chat (GET)

```
GET /chat?thread_id=<thread_id>&user_input=<query>
```

### Streaming Chat (POST)

```
POST /chat
```

Request body:
```json
{
  "thread_id": "conversation_1",
  "user_input": "What is the capital of France?"
}
```

## SSE Events

The streaming endpoints emit the following event types:

- **data**: Message content updates from agents
- **node_change**: Notification when processing moves to a different agent
- **progress**: Updates on the workflow progress
- **error**: Error messages if something goes wrong
- **complete**: Marks the end of the response stream

## AIMessage vs AIMessageChunk

The system supports two types of message streaming:

- **AIMessage**: Complete messages sent in their entirety
- **AIMessageChunk**: Incremental updates containing only new content

The agent nodes use AIMessageChunk for streaming intermediate results and AIMessage for final content, optimizing bandwidth usage while ensuring a smooth streaming experience. The difference is:

1. **AIMessageChunk**: Used for delta updates, containing only the new portion of text
2. **AIMessage**: Used for complete responses or final summaries

The streaming format can be identified in the SSE data event by checking the `is_chunk` field.

## Testing the Streaming Endpoint

You can test the streaming API with curl:

```bash
make run-sse-client
# or
curl -N "http://localhost:8000/chat?thread_id=test&user_input=What%20is%20the%20weather%20in%20Beijing?"
```

## Frontend Integration Example

Here's a simple example of integrating with the SSE endpoint in JavaScript:

```javascript
const eventSource = new EventSource('/chat?thread_id=12345&user_input=What%20is%20the%20weather%20in%20Beijing?');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Message:', data.content);

  // If it's a chunk, append to existing content
  if (data.is_chunk) {
    appendToExistingMessage(data.source, data.content);
  } else {
    // Otherwise create a new message
    createNewMessage(data.source, data.content);
  }
};

eventSource.addEventListener('node_change', (event) => {
  const data = JSON.parse(event.data);
  console.log('Node changed to:', data.node, data.description);
  // Update UI to show current agent
  updateActiveAgent(data.node, data.description);
});

eventSource.addEventListener('complete', (event) => {
  console.log('Stream complete');
  eventSource.close();
});

eventSource.addEventListener('error', (event) => {
  console.error('Error:', event);
  eventSource.close();
});
```
