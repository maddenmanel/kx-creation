"""
Demo script for KX Intelligent Content Creation System
Demonstrates the multi-agent workflow with AgentScope and Qwen
"""
import requests
import time
import json
from typing import Dict, Any


# Configuration
API_BASE_URL = "http://localhost:8000"  # Change to your API URL
DEMO_URL = "https://en.wikipedia.org/wiki/Artificial_intelligence"  # Example URL


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_json(data: Dict[Any, Any], indent: int = 2):
    """Pretty print JSON data"""
    print(json.dumps(data, indent=indent, ensure_ascii=False, default=str))


def check_health():
    """Check API health status"""
    print_section("Health Check")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        response.raise_for_status()
        
        data = response.json()
        print("✅ API is healthy!")
        print_json(data)
        return True
        
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        return False


def demo_url_to_article():
    """
    Demo: URL to Article workflow
    Crawls a URL, analyzes content, and creates an article
    """
    print_section("Demo 1: URL to Article Workflow")
    
    try:
        # Submit task
        print("📤 Submitting URL to Article task...")
        payload = {
            "url": DEMO_URL,
            "article_style": "professional",
            "target_audience": "general",
            "word_count": 800,
            "extract_images": True,
            "extract_links": True
        }
        
        print(f"Request payload:")
        print_json(payload)
        
        response = requests.post(
            f"{API_BASE_URL}/api/url-to-article",
            json=payload
        )
        response.raise_for_status()
        
        task_data = response.json()
        task_id = task_data["task_id"]
        print(f"\n✅ Task created! Task ID: {task_id}")
        
        # Poll for completion
        print("\n⏳ Waiting for task completion...")
        max_attempts = 60  # 2 minutes with 2-second intervals
        attempt = 0
        
        while attempt < max_attempts:
            time.sleep(2)
            attempt += 1
            
            status_response = requests.get(
                f"{API_BASE_URL}/api/task/{task_id}/status"
            )
            status_response.raise_for_status()
            status_data = status_response.json()
            
            status = status_data["status"]
            message = status_data["message"]
            progress = status_data.get("progress")
            
            print(f"Status: {status} - {message}")
            if progress:
                print(f"Progress: {progress}")
            
            if status == "completed":
                print("\n✅ Task completed successfully!")
                
                # Get result
                result_response = requests.get(
                    f"{API_BASE_URL}/api/task/{task_id}/result"
                )
                result_response.raise_for_status()
                result_data = result_response.json()
                
                # Display results
                print_section("Results")
                
                if result_data.get("data"):
                    data = result_data["data"]
                    
                    # Crawl result
                    if "crawl_result" in data:
                        print("📄 Crawl Result:")
                        crawl = data["crawl_result"]
                        print(f"  Title: {crawl.get('title')}")
                        print(f"  Content length: {len(crawl.get('content', ''))} characters")
                        print(f"  Images: {len(crawl.get('images', []))}")
                        print(f"  Links: {len(crawl.get('links', []))}")
                    
                    # Analysis result
                    if "analysis_result" in data:
                        print("\n🔍 Analysis Result:")
                        analysis = data["analysis_result"]
                        print(f"  Summary: {analysis.get('summary', '')[:200]}...")
                        print(f"  Key Points: {len(analysis.get('key_points', []))}")
                        print(f"  Themes: {', '.join(analysis.get('themes', []))}")
                    
                    # Article result
                    if "article_result" in data:
                        print("\n✍️  Article Result:")
                        article = data["article_result"]
                        print(f"  Title: {article.get('title')}")
                        print(f"  Word Count: {article.get('word_count')}")
                        print(f"  Style: {article.get('style')}")
                        print(f"\n  Content Preview:")
                        print(f"  {article.get('content', '')[:500]}...")
                
                return True
                
            elif status == "failed":
                print(f"\n❌ Task failed: {status_data.get('message')}")
                if result_data.get("error"):
                    print(f"Error: {result_data['error']}")
                return False
        
        print("\n⏱️ Timeout: Task took too long")
        return False
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False


def demo_step_by_step():
    """
    Demo: Step-by-step workflow
    Demonstrates individual agent operations
    """
    print_section("Demo 2: Step-by-Step Workflow")
    
    try:
        # Step 1: Crawl
        print("📡 Step 1: Crawling URL...")
        crawl_response = requests.post(
            f"{API_BASE_URL}/api/crawl",
            json={
                "url": DEMO_URL,
                "extract_images": False,
                "extract_links": False
            }
        )
        crawl_response.raise_for_status()
        crawl_result = crawl_response.json()
        print(f"✅ Crawled: {crawl_result.get('title')}")
        
        # Step 2: Analyze
        print("\n🔍 Step 2: Analyzing content...")
        analyze_response = requests.post(
            f"{API_BASE_URL}/api/analyze",
            json={
                "title": crawl_result.get("title"),
                "content": crawl_result.get("content")[:2000]  # Limit for demo
            }
        )
        analyze_response.raise_for_status()
        analysis_result = analyze_response.json()
        print(f"✅ Analysis complete")
        print(f"   Themes: {', '.join(analysis_result.get('themes', []))}")
        
        # Step 3: Write
        print("\n✍️  Step 3: Writing article...")
        write_response = requests.post(
            f"{API_BASE_URL}/api/write",
            json={
                "analysis_result": analysis_result,
                "article_style": "casual",
                "target_audience": "general",
                "word_count": 500
            }
        )
        write_response.raise_for_status()
        article_result = write_response.json()
        print(f"✅ Article created: {article_result.get('title')}")
        print(f"   Word count: {article_result.get('word_count')}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False


def main():
    """Run all demos"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "KX INTELLIGENT CONTENT CREATION SYSTEM" + " " * 20 + "║")
    print("║" + " " * 25 + "Multi-Agent Demo Script" + " " * 30 + "║")
    print("╚" + "=" * 78 + "╝")
    
    # Check health
    if not check_health():
        print("\n❌ API is not available. Please make sure the server is running.")
        print("   Start the server with: uvicorn client.main:app --reload")
        return
    
    print("\n" + "=" * 80)
    print("Choose a demo:")
    print("  1. URL to Article (Complete workflow)")
    print("  2. Step-by-step (Individual agents)")
    print("  3. Run all demos")
    print("  0. Exit")
    print("=" * 80)
    
    choice = input("\nEnter your choice (0-3): ").strip()
    
    if choice == "1":
        demo_url_to_article()
    elif choice == "2":
        demo_step_by_step()
    elif choice == "3":
        demo_url_to_article()
        time.sleep(2)
        demo_step_by_step()
    elif choice == "0":
        print("\n👋 Goodbye!")
        return
    else:
        print("\n❌ Invalid choice")
        return
    
    print("\n" + "=" * 80)
    print("✨ Demo completed!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()

