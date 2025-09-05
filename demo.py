#!/usr/bin/env python3
"""
KX智能内容创作系统 - 演示脚本
"""
import requests
import time
import json
from typing import Dict, Any


class KXCreationClient:
    """KX智能内容创作系统客户端"""
    
    def __init__(self, base_url: str = "http://localhost"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def health_check(self) -> bool:
        """健康检查"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            return response.status_code == 200
        except:
            return False
    
    def crawl_page(self, url: str, extract_images: bool = True, extract_links: bool = True) -> Dict[str, Any]:
        """爬取页面"""
        response = self.session.post(f"{self.base_url}/api/crawl", json={
            "url": url,
            "extract_images": extract_images,
            "extract_links": extract_links
        })
        return response.json()
    
    def url_to_article(
        self,
        url: str,
        article_style: str = "professional",
        target_audience: str = "general",
        word_count: int = None
    ) -> str:
        """URL转文章（异步任务）"""
        # 提交任务
        response = self.session.post(f"{self.base_url}/api/url-to-article", json={
            "url": url,
            "article_style": article_style,
            "target_audience": target_audience,
            "word_count": word_count,
            "extract_images": True,
            "extract_links": True
        })
        
        if response.status_code != 200:
            raise Exception(f"任务提交失败: {response.text}")
        
        task_data = response.json()
        task_id = task_data["task_id"]
        
        print(f"任务已提交，任务ID: {task_id}")
        print("正在处理中...")
        
        # 轮询任务状态
        while True:
            status_response = self.session.get(f"{self.base_url}/api/task/{task_id}/status")
            if status_response.status_code != 200:
                raise Exception(f"获取任务状态失败: {status_response.text}")
            
            status = status_response.json()
            print(f"任务状态: {status['status']}, 进度: {status['progress']}%, 消息: {status['message']}")
            
            if status["status"] == "completed":
                # 获取结果
                result_response = self.session.get(f"{self.base_url}/api/task/{task_id}/result")
                if result_response.status_code != 200:
                    raise Exception(f"获取任务结果失败: {result_response.text}")
                
                result = result_response.json()
                if result["success"]:
                    return result["data"]
                else:
                    raise Exception(f"任务失败: {result['message']}")
                    
            elif status["status"] == "failed":
                raise Exception(f"任务失败: {status['message']}")
            
            time.sleep(2)
    
    def url_to_wechat(
        self,
        url: str,
        article_style: str = "professional",
        target_audience: str = "general",
        author: str = None,
        draft_only: bool = True
    ) -> str:
        """URL到微信发布（异步任务）"""
        # 提交任务
        response = self.session.post(f"{self.base_url}/api/url-to-wechat", json={
            "url": url,
            "article_style": article_style,
            "target_audience": target_audience,
            "author": author,
            "draft_only": draft_only,
            "extract_images": True,
            "extract_links": True
        })
        
        if response.status_code != 200:
            raise Exception(f"任务提交失败: {response.text}")
        
        task_data = response.json()
        task_id = task_data["task_id"]
        
        print(f"任务已提交，任务ID: {task_id}")
        print("正在处理中...")
        
        # 轮询任务状态
        while True:
            status_response = self.session.get(f"{self.base_url}/api/task/{task_id}/status")
            if status_response.status_code != 200:
                raise Exception(f"获取任务状态失败: {status_response.text}")
            
            status = status_response.json()
            print(f"任务状态: {status['status']}, 进度: {status['progress']}%, 消息: {status['message']}")
            
            if status["status"] == "completed":
                # 获取结果
                result_response = self.session.get(f"{self.base_url}/api/task/{task_id}/result")
                if result_response.status_code != 200:
                    raise Exception(f"获取任务结果失败: {result_response.text}")
                
                result = result_response.json()
                if result["success"]:
                    return result["data"]
                else:
                    raise Exception(f"任务失败: {result['message']}")
                    
            elif status["status"] == "failed":
                raise Exception(f"任务失败: {status['message']}")
            
            time.sleep(2)


def demo_crawl_page():
    """演示页面爬取功能"""
    print("\n" + "="*50)
    print("🕷️ 演示页面爬取功能")
    print("="*50)
    
    client = KXCreationClient()
    
    # 检查服务状态
    if not client.health_check():
        print("❌ 服务未启动，请先启动服务")
        return
    
    # 爬取示例页面
    test_url = "https://www.example.com"
    print(f"正在爬取页面: {test_url}")
    
    try:
        result = client.crawl_page(test_url)
        if result.get("success"):
            page_data = result["data"]["page_content"]
            print(f"✅ 爬取成功!")
            print(f"标题: {page_data['title']}")
            print(f"内容长度: {len(page_data['content'])} 字符")
            print(f"图片数量: {len(page_data['images'])}")
            print(f"链接数量: {len(page_data['links'])}")
        else:
            print(f"❌ 爬取失败: {result.get('message')}")
    except Exception as e:
        print(f"❌ 爬取出错: {str(e)}")


def demo_url_to_article():
    """演示URL转文章功能"""
    print("\n" + "="*50)
    print("✍️ 演示URL转文章功能")
    print("="*50)
    
    client = KXCreationClient()
    
    # 检查服务状态
    if not client.health_check():
        print("❌ 服务未启动，请先启动服务")
        return
    
    # 转换示例文章
    test_url = "https://www.example.com"
    print(f"正在处理URL: {test_url}")
    print("文章风格: professional")
    print("目标受众: general")
    
    try:
        result = client.url_to_article(
            url=test_url,
            article_style="professional",
            target_audience="general"
        )
        
        article = result["article_result"]["article"]
        print(f"\n✅ 文章创作完成!")
        print(f"标题: {article['title']}")
        print(f"字数: {article['word_count']}")
        print(f"摘要: {article['summary']}")
        print(f"标签: {', '.join(article['tags'])}")
        print(f"\n内容预览:")
        print(article['content'][:200] + "..." if len(article['content']) > 200 else article['content'])
        
        # 显示处理时间
        processing_time = result["processing_time"]
        print(f"\n⏱️ 处理时间:")
        print(f"爬取: {processing_time['crawl']:.2f}秒")
        print(f"分析: {processing_time['analyze']:.2f}秒")
        print(f"写作: {processing_time['write']:.2f}秒")
        print(f"总计: {processing_time['total']:.2f}秒")
        
    except Exception as e:
        print(f"❌ 处理出错: {str(e)}")


def demo_url_to_wechat():
    """演示URL到微信发布功能"""
    print("\n" + "="*50)
    print("📱 演示URL到微信发布功能")
    print("="*50)
    
    client = KXCreationClient()
    
    # 检查服务状态
    if not client.health_check():
        print("❌ 服务未启动，请先启动服务")
        return
    
    # 发布示例文章
    test_url = "https://www.example.com"
    print(f"正在处理URL: {test_url}")
    print("文章风格: professional")
    print("目标受众: general")
    print("模式: 仅创建草稿")
    
    try:
        result = client.url_to_wechat(
            url=test_url,
            article_style="professional",
            target_audience="general",
            author="KX智能创作",
            draft_only=True  # 仅创建草稿，不直接发布
        )
        
        print(f"\n✅ 完整流程处理完成!")
        
        # 显示文章信息
        article_process = result["article_process"]
        article = article_process["article_result"]["article"]
        print(f"\n📝 文章信息:")
        print(f"标题: {article['title']}")
        print(f"字数: {article['word_count']}")
        
        # 显示发布信息
        if result.get("publish_process"):
            publish_result = result["publish_process"]["publish_result"]
            print(f"\n📱 微信发布:")
            print(f"状态: {publish_result['success']}")
            print(f"消息: {publish_result['message']}")
            if publish_result.get("media_id"):
                print(f"草稿ID: {publish_result['media_id']}")
        
        # 显示总处理时间
        total_time = result["total_processing_time"]
        print(f"\n⏱️ 总处理时间: {total_time:.2f}秒")
        
    except Exception as e:
        print(f"❌ 处理出错: {str(e)}")


def main():
    """主函数"""
    print("🚀 KX智能内容创作系统 - 演示程序")
    print("请确保已启动服务: ./deploy.sh")
    print("API文档: http://localhost/docs")
    
    while True:
        print("\n" + "="*50)
        print("请选择演示功能:")
        print("1. 页面爬取演示")
        print("2. URL转文章演示")
        print("3. URL到微信发布演示")
        print("4. 退出")
        print("="*50)
        
        choice = input("请输入选项 (1-4): ").strip()
        
        if choice == "1":
            demo_crawl_page()
        elif choice == "2":
            demo_url_to_article()
        elif choice == "3":
            demo_url_to_wechat()
        elif choice == "4":
            print("👋 再见!")
            break
        else:
            print("❌ 无效选项，请重新选择")


if __name__ == "__main__":
    main()
