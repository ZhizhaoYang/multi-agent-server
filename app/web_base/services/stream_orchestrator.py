import json
from typing import Dict, Callable, Optional, Any


class StreamEventConverter:
    """Lightweight utility for converting stream events to client format"""

    @staticmethod
    def format_sse_message(chunk_text: str, chunk_type: str, **kwargs) -> str:
        """Format a message for Server-Sent Events (SSE) streaming"""
        data = {"chunk": chunk_text, "type": chunk_type}
        data.update(kwargs)
        return f"data: {json.dumps(data)}\n\n"

    @classmethod
    def convert_queue_event(cls, event) -> Optional[str]:
        """Convert queue events to client format"""
        handlers = {
            "thought": lambda: cls.format_sse_message(
                event.content,
                'thought',
                source=event.source,
                segment_id=event.segment_id,
                timestamp=event.timestamp.isoformat() if hasattr(event.timestamp, 'isoformat') else str(event.timestamp)
            ),
            "thought_complete": lambda: cls.format_sse_message(
                "",
                'thought_complete',
                source=event.source,
                segment_id=event.segment_id,
                total_length=event.metadata.get('total_length', 0)
            )
        }

        handler = handlers.get(event.event_type)
        return handler() if handler else None

    @classmethod
    def convert_graph_event(cls, stream_content: Dict[str, Any]) -> Optional[str]:
        """Convert graph events to client format"""
        message_type = stream_content.get('type', 'final_output')

        if message_type == 'thought':
            thought_content = stream_content.get('thought_content', '')
            if thought_content:
                return cls.format_sse_message(
                    thought_content,
                    'thought',
                    source=stream_content.get('source', ''),
                    segment_id=stream_content.get('segment_id', 0),
                    timestamp=stream_content.get('timestamp', '')
                )
        elif message_type == 'thought_complete':
            return cls.format_sse_message(
                "",
                'thought_complete',
                source=stream_content.get('source', ''),
                segment_id=stream_content.get('segment_id', 0),
                total_length=stream_content.get('total_length', 0)
            )
        elif message_type == 'final_output':
            final_output_str = stream_content.get('final_output', '')
            if final_output_str:
                return cls.format_sse_message(final_output_str, 'final_output')

        return None

    @classmethod
    def format_final_result(cls, thread_id: str, final_output: str) -> str:
        """Format the final result message"""
        result = {
            "thread_id": thread_id,
            "final_output": final_output,
        }
        return f"data: {json.dumps(result)}\n\n"