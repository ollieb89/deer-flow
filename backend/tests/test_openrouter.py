import unittest
from unittest.mock import MagicMock, patch

from src.models.openrouter import ChatOpenRouter
from langchain_core.messages import AIMessage


class TestChatOpenRouter(unittest.TestCase):
    def test_initialization_defaults(self):
        """Test that defaults are correctly set."""
        model = ChatOpenRouter(api_key="test-key")
        self.assertEqual(model.openai_api_base, "https://openrouter.ai/api/v1")
        # Check default headers in the underlying client params if possible, 
        # or just verify our property logic.
        
    def test_headers_logic(self):
        """Test that OpenRouter headers are correctly merged."""
        model = ChatOpenRouter(
            api_key="test-key",
            default_headers={"X-Custom": "value"},
            referer="https://custom.com",
            title="CustomApp"
        )
        # default_headers is passed to the super().__init__ which sets it on the client
        # In langchain-openai 1.1.7, it's stored in model.default_headers
        self.assertEqual(model.default_headers["HTTP-Referer"], "https://custom.com")
        self.assertEqual(model.default_headers["X-OpenRouter-Title"], "CustomApp")
        self.assertEqual(model.default_headers["X-Custom"], "value")

    def test_base_url_logic(self):
        """Test that base_url is correctly handled."""
        # Case 1: Default
        model1 = ChatOpenRouter(api_key="test-key")
        self.assertEqual(model1.openai_api_base, "https://openrouter.ai/api/v1")
        
        # Case 2: Custom api_base
        model2 = ChatOpenRouter(api_key="test-key", api_base="https://custom.ai/v1")
        # super().__init__ will use base_url if provided, but our class uses api_base to set base_url
        self.assertEqual(model2.openai_api_base, "https://openrouter.ai/api/v1")
        # The key is what's passed to super().__init__ via kwargs
        
    def test_reasoning_extraction(self):
        """Test that reasoning is extracted from the response."""
        model = ChatOpenRouter(api_key="test-key")
        
        # Mock response object
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Hello"
        mock_message.reasoning = "Thinking..."
        mock_message.role = "assistant"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_response.model = "test-model"
        mock_response.id = "test-id"
        mock_response.usage = MagicMock()
        
        with patch("langchain_openai.chat_models.base.ChatOpenAI._create_chat_result") as mock_super:
            # Setup mock_super to return a basic ChatResult
            from langchain_core.outputs import ChatResult, ChatGeneration
            from langchain_core.messages import AIMessage
            
            mock_super.return_value = ChatResult(
                generations=[ChatGeneration(message=AIMessage(content="Hello"))]
            )
            
            result = model._create_chat_result(mock_response)
            
            self.assertEqual(result.generations[0].message.additional_kwargs["reasoning"], "Thinking...")

if __name__ == "__main__":
    unittest.main()
