"""
Claude API integration service.
Handles all communication with the Anthropic Claude API.
"""

import json
from typing import List, Dict, Any, Optional
from anthropic import Anthropic
from app.config import get_settings

settings = get_settings()


class ClaudeService:
    """Service for interacting with Claude API."""

    def __init__(self):
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-sonnet-4-20250514"

    def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 1024
    ) -> Dict[str, Any]:
        """
        Send a message to Claude and get a response.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: The system prompt defining agent behavior
            tools: Optional list of tool definitions
            max_tokens: Maximum tokens in response

        Returns:
            Claude's response with content and any tool calls
        """
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": system_prompt,
            "messages": messages,
        }

        if tools:
            kwargs["tools"] = tools

        response = self.client.messages.create(**kwargs)

        return {
            "id": response.id,
            "content": response.content,
            "stop_reason": response.stop_reason,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            }
        }

    def extract_tool_calls(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract tool calls from a Claude response."""
        tool_calls = []
        for block in response.get("content", []):
            if hasattr(block, "type") and block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                })
        return tool_calls

    def extract_text(self, response: Dict[str, Any]) -> str:
        """Extract text content from a Claude response."""
        text_parts = []
        for block in response.get("content", []):
            if hasattr(block, "type") and block.type == "text":
                text_parts.append(block.text)
        return "\n".join(text_parts)


# Singleton instance
claude_service = ClaudeService()
