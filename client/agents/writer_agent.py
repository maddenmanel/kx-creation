"""
Writer Agent for article creation
Uses Qwen LLM to generate high-quality articles
"""
from typing import Optional, Dict, Any
from agentscope.message import Msg
from loguru import logger
import json

from .base_agent import KXBaseAgent


class WriterAgent(KXBaseAgent):
    """
    Writer Agent for intelligent article creation
    Creates articles based on analysis results with specified style and audience
    """
    
    # Style templates
    STYLE_TEMPLATES = {
        "professional": {
            "tone": "formal and authoritative",
            "structure": "well-organized with clear sections",
            "language": "precise and technical terminology",
            "features": "data-driven, objective, evidence-based"
        },
        "casual": {
            "tone": "friendly and conversational",
            "structure": "flexible and engaging",
            "language": "everyday language with relatable examples",
            "features": "personal anecdotes, humor, accessibility"
        },
        "news": {
            "tone": "objective and factual",
            "structure": "inverted pyramid (most important first)",
            "language": "clear, concise, and neutral",
            "features": "who, what, when, where, why, how"
        }
    }
    
    # Audience profiles
    AUDIENCE_PROFILES = {
        "general": "general public with varied backgrounds and interests",
        "technical": "technical professionals with specialized knowledge",
        "business": "business professionals focused on practical applications"
    }
    
    def __init__(
        self,
        name: str = "WriterAgent",
        model: Optional[Any] = None,
        **kwargs
    ):
        """Initialize Writer Agent"""
        self.model = model
        sys_prompt = """You are an expert content writer and editor. Your role is to:

1. Create high-quality, engaging articles based on provided analysis
2. Adapt writing style to match specified requirements
3. Target specific audiences effectively
4. Maintain consistent tone and voice throughout
5. Ensure proper structure and flow
6. Generate compelling titles and summaries

When writing articles, you should:
- Follow the specified writing style (professional/casual/news)
- Target the appropriate audience
- Meet word count requirements
- Create clear, logical structure
- Use engaging and relevant examples
- Include proper transitions between sections

Output format should be JSON with:
{
    "title": "Compelling article title",
    "content": "Full article content with proper formatting",
    "summary": "Brief summary (2-3 sentences)",
    "tags": ["tag1", "tag2", ...],
    "word_count": integer
}"""
        
        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            **kwargs
        )
    
    def reply(self, x: Optional[Msg] = None) -> Msg:
        """
        Process writing request
        
        Args:
            x: Message containing writing request with analysis and parameters
            
        Returns:
            Message with article content
        """
        try:
            if not self._validate_input(x):
                return self._create_message(
                    {"error": "Invalid input message"},
                    metadata={"status": "failed"}
                )
            
            request_data = x.content if isinstance(x.content, dict) else {}
            analysis_result = request_data.get("analysis_result", {})
            article_style = request_data.get("article_style", "professional")
            target_audience = request_data.get("target_audience", "general")
            word_count = request_data.get("word_count", 1000)
            
            if not analysis_result:
                logger.warning(f"{self.name}: No analysis result provided")
                return self._create_message(
                    {"error": "No analysis result provided"},
                    metadata={"status": "failed"}
                )
            
            logger.info(f"{self.name}: Writing article (style={article_style}, audience={target_audience}, words={word_count})")
            
            # Get style and audience information
            style_info = self.STYLE_TEMPLATES.get(article_style, self.STYLE_TEMPLATES["professional"])
            audience_desc = self.AUDIENCE_PROFILES.get(target_audience, self.AUDIENCE_PROFILES["general"])
            
            # Create writing prompt
            writing_prompt = f"""Based on the following content analysis, write a comprehensive article:

ANALYSIS:
Summary: {analysis_result.get('summary', '')}
Key Points: {', '.join(analysis_result.get('key_points', []))}
Themes: {', '.join(analysis_result.get('themes', []))}
Recommendations: {', '.join(analysis_result.get('recommendations', []))}

WRITING REQUIREMENTS:
- Style: {article_style} ({style_info['tone']})
- Structure: {style_info['structure']}
- Language: {style_info['language']}
- Features: {style_info['features']}
- Target Audience: {audience_desc}
- Target Word Count: {word_count} words

Please write a complete article that:
1. Has a compelling and SEO-friendly title
2. Follows the specified style guidelines
3. Targets the appropriate audience
4. Covers all key points from the analysis
5. Has proper structure with introduction, body, and conclusion
6. Includes relevant examples and supporting details
7. Meets the word count target

Provide the output in the specified JSON format."""
            
            # Call model for writing
            prompt_msg = Msg(
                name="user",
                content=writing_prompt,
                role="user"
            )
            
            # Use model to generate article
            response = self.model(prompt_msg)
            
            # Parse response
            try:
                response_text = response.content if hasattr(response, 'content') else str(response)
                
                # Find JSON in response
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx]
                    article_result = json.loads(json_str)
                else:
                    # Fallback: create structured response
                    article_result = self._create_fallback_article(
                        response_text,
                        analysis_result,
                        article_style,
                        word_count
                    )
                
                # Ensure all required fields
                article_result.setdefault("title", "Untitled Article")
                article_result.setdefault("content", response_text)
                article_result.setdefault("summary", analysis_result.get('summary', '')[:200])
                article_result.setdefault("tags", analysis_result.get('themes', []))
                article_result.setdefault("word_count", len(response_text.split()))
                article_result["style"] = article_style
                
            except json.JSONDecodeError:
                logger.warning(f"{self.name}: Failed to parse JSON response, using fallback")
                article_result = self._create_fallback_article(
                    response.content if hasattr(response, 'content') else str(response),
                    analysis_result,
                    article_style,
                    word_count
                )
            
            logger.info(f"{self.name}: Article created successfully ({article_result.get('word_count', 0)} words)")
            
            return self._create_message(
                article_result,
                metadata={
                    "status": "success",
                    "style": article_style,
                    "word_count": article_result.get("word_count", 0)
                }
            )
            
        except Exception as e:
            self._log_error(e, "reply")
            return self._create_message(
                {"error": str(e)},
                metadata={"status": "failed"}
            )
    
    def _create_fallback_article(
        self,
        response_text: str,
        analysis_result: Dict[str, Any],
        style: str,
        word_count: int
    ) -> Dict[str, Any]:
        """
        Create fallback article structure when JSON parsing fails
        
        Args:
            response_text: Raw response text from model
            analysis_result: Analysis results
            style: Article style
            word_count: Target word count
            
        Returns:
            Structured article result
        """
        # Extract title from first line or use summary
        lines = [line.strip() for line in response_text.split('\n') if line.strip()]
        title = lines[0] if lines else analysis_result.get('summary', 'Article')[:100]
        
        # Clean title
        if title.lower().startswith('title:'):
            title = title[6:].strip()
        
        # Use response as content
        content = response_text
        
        return {
            "title": title,
            "content": content,
            "summary": analysis_result.get('summary', '')[:200],
            "tags": analysis_result.get('themes', [])[:5],
            "word_count": len(content.split()),
            "style": style
        }
    
    def write(
        self,
        analysis_result: Dict[str, Any],
        article_style: str = "professional",
        target_audience: str = "general",
        word_count: int = 1000
    ) -> Dict[str, Any]:
        """
        Convenience method to write an article
        
        Args:
            analysis_result: Analysis results from AnalyzerAgent
            article_style: Writing style (professional/casual/news)
            target_audience: Target audience (general/technical/business)
            word_count: Target word count
            
        Returns:
            Article result as dictionary
        """
        try:
            if not analysis_result:
                logger.warning(f"{self.name}: No analysis result provided")
                return {"error": "No analysis result provided"}
            
            logger.info(f"{self.name}: Writing article (style={article_style}, audience={target_audience}, words={word_count})")
            
            # Get style and audience information
            style_info = self.STYLE_TEMPLATES.get(article_style, self.STYLE_TEMPLATES["professional"])
            audience_desc = self.AUDIENCE_PROFILES.get(target_audience, self.AUDIENCE_PROFILES["general"])
            
            # Create writing prompt
            writing_prompt = f"""Based on the following content analysis, write a comprehensive article:

ANALYSIS:
Summary: {analysis_result.get('summary', '')}
Key Points: {', '.join(analysis_result.get('key_points', []))}
Themes: {', '.join(analysis_result.get('themes', []))}

REQUIREMENTS:
- Style: {article_style} - {style_info['tone']}
- Target Audience: {audience_desc}
- Target Word Count: {word_count} words

Write a complete article with:
1. A compelling SEO-friendly title
2. Well-structured content (introduction, body, conclusion)
3. Covers all key points
4. Meets the word count target

Provide output in JSON format with keys: title, content, summary, tags (list), word_count"""
            
            # Call model for writing
            if self.model:
                try:
                    import asyncio
                    # Call async model synchronously
                    response = asyncio.run(self.model([{"role": "user", "content": writing_prompt}]))
                    response_text = response.text if hasattr(response, 'text') else str(response)
                    
                    # Try to extract JSON
                    import json
                    start_idx = response_text.find('{')
                    end_idx = response_text.rfind('}') + 1
                    
                    if start_idx != -1 and end_idx > start_idx:
                        json_str = response_text[start_idx:end_idx]
                        article_result = json.loads(json_str)
                    else:
                        article_result = self._create_fallback_article(response_text, analysis_result, article_style, word_count)
                except Exception as e:
                    logger.warning(f"{self.name}: Model call failed: {e}, using fallback")
                    article_result = self._create_fallback_article("Failed to generate", analysis_result, article_style, word_count)
            else:
                article_result = self._create_fallback_article("No model available", analysis_result, article_style, word_count)
            
            # Ensure required fields
            article_result.setdefault("title", "Untitled Article")
            article_result.setdefault("content", "Content not generated")
            article_result.setdefault("summary", analysis_result.get('summary', '')[:200])
            article_result.setdefault("tags", analysis_result.get('themes', []))
            article_result.setdefault("word_count", len(article_result.get("content", "").split()))
            article_result["style"] = article_style
            
            logger.info(f"{self.name}: Article created successfully ({article_result.get('word_count', 0)} words)")
            return article_result
            
        except Exception as e:
            logger.error(f"{self.name}: Writing error: {str(e)}")
            return {"error": str(e)}

