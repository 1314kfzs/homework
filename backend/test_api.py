#!/usr/bin/env python3
"""
API 测试脚本
用于测试后端服务是否正常运行
"""

import requests
import json
import time

# 配置
BASE_URL = "http://127.0.0.1:8001"
OLLAMA_URL = "http://127.0.0.1:11434"

def test_ollama_connection():
    """测试 Ollama 连接"""
    print("测试 Ollama 连接...")
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=10)
        if response.status_code == 200:
            print("✅ Ollama 连接正常")
            models = response.json().get('models', [])
            if models:
                print(f"✅ 可用模型: {[m['name'] for m in models]}")
            else:
                print("⚠️ 未找到模型，请运行: ollama pull qwen2.5:7b")
            return True
        else:
            print("❌ Ollama 连接失败")
            return False
    except Exception as e:
        print(f"❌ Ollama 连接错误: {e}")
        return False

def test_backend_health():
    """测试后端健康状态"""
    print("\n测试后端健康状态...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ 后端服务健康")
            print(f"   状态: {data.get('status')}")
            print(f"   Ollama连接: {data.get('ollama_connection')}")
            return True
        else:
            print(f"❌ 后端健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 后端连接错误: {e}")
        return False

def test_search_api():
    """测试搜索 API"""
    print("\n测试搜索 API...")
    try:
        payload = {
            "query": "machine learning",
            "max_results": 5,
            "page": 1,
            "page_size": 3
        }
        
        response = requests.post(f"{BASE_URL}/search", json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            papers = data.get('papers', [])
            print(f"✅ 搜索成功，找到 {len(papers)} 篇论文")
            
            if papers:
                print("📄 论文示例:")
                for i, paper in enumerate(papers[:2]):  # 只显示前2篇
                    print(f"   {i+1}. {paper['title'][:50]}...")
                    print(f"      作者: {', '.join(paper['authors'][:2])}...")
                    print(f"      发布时间: {paper['published']}")
            return True
        else:
            print(f"❌ 搜索失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 搜索测试错误: {e}")
        return False

def test_ask_api():
    """测试问答 API"""
    print("\n测试问答 API...")
    try:
        payload = {
            "query": "machine learning",
            "question": "什么是机器学习的主要应用领域？",
            "max_results": 3,
            "top_k": 2
        }
        
        print("🤖 正在向 AI 提问...")
        start_time = time.time()
        
        response = requests.post(f"{BASE_URL}/ask", json=payload, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get('answer', '')
            citations = data.get('citations', [])
            
            elapsed_time = time.time() - start_time
            print(f"✅ 问答成功 (耗时: {elapsed_time:.2f}s)")
            print(f"📝 AI 回答: {answer[:100]}...")
            print(f"📚 引用来源: {len(citations)} 个")
            
            if citations:
                print("📄 引用论文:")
                for i, citation in enumerate(citations[:2]):
                    print(f"   {i+1}. {citation['title'][:50]}...")
            return True
        else:
            print(f"❌ 问答失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 问答测试错误: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("ArXiv RAG 系统测试")
    print("=" * 50)
    
    # 测试顺序
    tests = [
        ("Ollama 连接", test_ollama_connection),
        ("后端健康检查", test_backend_health),
        ("搜索功能", test_search_api),
        ("问答功能", test_ask_api)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            results.append((test_name, False))
        
        time.sleep(1)  # 短暂延迟
    
    # 汇总结果
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    
    all_passed = True
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")
        if not success:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 所有测试通过！系统运行正常")
        print("\n下一步:")
        print("1. 启动前端: cd frontend && npm run dev")
        print("2. 访问 http://127.0.0.1:5173")
        print("3. 开始使用论文搜索引擎")
    else:
        print("⚠️ 部分测试失败，请检查配置")
        print("\n故障排除建议:")
        print("1. 确保 Ollama 服务运行: ollama serve")
        print("2. 检查后端服务: python run.py")
        print("3. 验证网络连接和端口")
        print("4. 查看详细错误日志")
    
    print("=" * 50)

if __name__ == "__main__":
    main()