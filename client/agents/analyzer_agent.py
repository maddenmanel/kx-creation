"""
Analyzer Agent for content analysis
Uses Qwen LLM to analyze and understand content
"""
from typing import Optional, Dict, Any
from agentscope.message import Msg
from loguru import logger
import json

from .base_agent import KXBaseAgent


class AnalyzerAgent(KXBaseAgent):
    """
    Analyzer Agent for intelligent content analysis
    Analyzes content structure, themes, key points and sentiment
    """
    
    def __init__(
        self,
        name: str = "AnalyzerAgent",
        model: Optional[Any] = None,
        **kwargs
    ):
        """Initialize Analyzer Agent"""
        self.model = model
        sys_prompt = """You are an expert content analyst. Your role is to:

1. Analyze content structure and organization
2. Identify main themes and topics
3. Extract key points and important information
4. Determine content sentiment and tone
5. Provide actionable recommendations for content creation

When analyzing content, provide:
- **Summary**: A concise summary of the main content
- **Key Points**: List of the most important points (3-7 items)
- **Themes**: Main themes and topics covered
- **Sentiment**: Overall sentiment (positive/neutral/negative) and tone
- **Structure**: Analysis of how content is organized
- **Recommendations**: Suggestions for creating new content based on this analysis

Always provide output in JSON format with these exact keys:
{
    "summary": "string",
    "key_points": ["point1", "point2", ...],
    "themes": ["theme1", "theme2", ...],
    "sentiment": "string",
    "structure": {"type": "string", "sections": [...], "flow": "string"},
    "recommendations": ["rec1", "rec2", ...]
}"""
        
        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            **kwargs
        )
    
    def reply(self, x: Optional[Msg] = None) -> Msg:
        """
        Process analysis request
        
        Args:
            x: Message containing content to analyze
            
        Returns:
            Message with analysis results
        """
        try:
            if not self._validate_input(x):
                return self._create_message(
                    {"error": "Invalid input message"},
                    metadata={"status": "failed"}
                )
            
            content_data = x.content if isinstance(x.content, dict) else {}
            title = content_data.get("title", "")
            content = content_data.get("content", "")
            
            if not content:
                logger.warning(f"{self.name}: No content provided for analysis")
                return self._create_message(
                    {"error": "No content provided"},
                    metadata={"status": "failed"}
                )
            
            logger.info(f"{self.name}: Analyzing content: {title[:50]}...")
            
            # Create analysis prompt
            analysis_prompt = f"""Analyze the following content and provide a comprehensive analysis:

Title: {title}

Content:
{content[:4000]}  # Limit content length for API

Please provide a detailed analysis in the specified JSON format."""
            
            # Call model for analysis
            prompt_msg = Msg(
                name="user",
                content=analysis_prompt,
                role="user"
            )
            
            # Use model to generate analysis
            response = self.model(prompt_msg)
            
            # Parse response
            try:
                # Try to extract JSON from response
                response_text = response.content if hasattr(response, 'content') else str(response)
                
                # Find JSON in response
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx]
                    analysis_result = json.loads(json_str)
                else:
                    # Fallback: create structured response from text
                    analysis_result = self._create_fallback_analysis(response_text, title, content)
                
            except json.JSONDecodeError:
                logger.warning(f"{self.name}: Failed to parse JSON response, using fallback")
                analysis_result = self._create_fallback_analysis(
                    response.content if hasattr(response, 'content') else str(response),
                    title,
                    content
                )
            
            logger.info(f"{self.name}: Analysis completed successfully")
            
            return self._create_message(
                analysis_result,
                metadata={
                    "status": "success",
                    "title": title
                }
            )
            
        except Exception as e:
            self._log_error(e, "reply")
            return self._create_message(
                {"error": str(e)},
                metadata={"status": "failed"}
            )
    
    def _create_fallback_analysis(self, response_text: str, title: str, content: str) -> Dict[str, Any]:
        """
        Create a fallback analysis structure when JSON parsing fails
        
        Args:
            response_text: Raw response text from model
            title: Content title
            content: Content body
            
        Returns:
            Structured analysis result
        """
        # Extract sentences from response
        sentences = [s.strip() for s in response_text.split('.') if s.strip()]
        
        return {
            "summary": sentences[0] if sentences else f"Analysis of: {title}",
            "key_points": sentences[1:4] if len(sentences) > 1 else [
                "Main content focus",
                "Supporting details",
                "Key takeaways"
            ],
            "themes": ["Information", "Knowledge", "Content"],
            "sentiment": "neutral",
            "structure": {
                "type": "article",
                "sections": ["introduction", "body", "conclusion"],
                "flow": "linear"
            },
            "recommendations": [
                "Expand on key points",
                "Add supporting examples",
                "Include relevant data and statistics"
            ]
        }
    
    def analyze(self, title: str, content: str, images: Optional[list] = None, links: Optional[list] = None) -> Dict[str, Any]:
        """
        Convenience method to analyze content
        
        Args:
            title: Content title
            content: Content body
            images: Optional list of image URLs
            links: Optional list of links
            
        Returns:
            Analysis results as dictionary
        """
        try:
            if not content:
                logger.warning(f"{self.name}: No content provided for analysis")
                return {"error": "No content provided"}
            
            logger.info(f"{self.name}: Analyzing content: {title[:50]}...")
            
            # Create analysis prompt
            analysis_prompt = f"""Analyze the following content and provide a comprehensive analysis:

Title: {title}

Content:
{content[:4000]}

Please provide a detailed analysis in JSON format with these keys:
- summary: A concise summary
- key_points: List of 3-7 main points
- themes: Main themes (list)
- sentiment: Overall sentiment
- structure: Content structure analysis (dict)
- recommendations: Writing recommendations (list)"""
            
            # Call model for analysis
            if self.model:
                try:
                    import asyncio
                    # Call async model synchronously
                    response = asyncio.run(self.model([{"role": "user", "content": analysis_prompt}]))
                    response_text = response.text if hasattr(response, 'text') else str(response)
                    
                    # Try to extract JSON
                    import json
                    start_idx = response_text.find('{')
                    end_idx = response_text.rfind('}') + 1
                    
                    if start_idx != -1 and end_idx > start_idx:
                        json_str = response_text[start_idx:end_idx]
                        analysis_result = json.loads(json_str)
                    else:
                        analysis_result = self._create_fallback_analysis(response_text, title, content)
                except Exception as e:
                    logger.warning(f"{self.name}: Model call failed: {e}, using fallback")
                    analysis_result = self._create_fallback_analysis("", title, content)
            else:
                analysis_result = self._create_fallback_analysis("", title, content)
            
            logger.info(f"{self.name}: Analysis completed successfully")
            return analysis_result
            
        except Exception as e:
            logger.error(f"{self.name}: Analysis error: {str(e)}")
            return {"error": str(e)}

