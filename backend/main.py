from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import requests
import json
import arxiv
import os
from datetime import datetime
import logging
import asyncio
import faiss
import numpy as np
import pickle
from pathlib import Path

# 简单的文本相似度计算，避免复杂的依赖
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ArXiv RAG API", version="1.0.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://172.27.144.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
VECTOR_DB_PATH = Path("data/vector_db.pkl")

# 数据模型
class SearchRequest(BaseModel):
    query: str
    max_results: int = 20
    sort_by: str = "relevance"
    page: int = 1
    page_size: int = 10

class AskRequest(BaseModel):
    query: str
    question: str
    max_results: int = 5
    top_k: int = 5

class Paper(BaseModel):
    paper_id: str
    title: str
    authors: List[str]
    summary: str
    published: str
    updated: str
    arxiv_url: str
    pdf_url: Optional[str] = None

class Citation(BaseModel):
    paper_id: str
    title: str
    authors: List[str]
    arxiv_url: str
    pdf_url: Optional[str]
    chunk_index: int
    content: str

class SearchResponse(BaseModel):
    papers: List[Paper]
    page: int
    total_pages: int
    total: int

class AskResponse(BaseModel):
    answer: str
    citations: List[Citation]

# 向量数据库类
class VectorDB:
    def __init__(self):
        self.index = None
        self.papers = []
        self.chunks = []
        self.embeddings = []
        
    def add_papers(self, papers: List[Paper]):
        """添加论文到向量数据库"""
        for paper in papers:
            # 将论文摘要分成多个chunk
            chunk_size = 500
            summary_chunks = [paper.summary[i:i+chunk_size] for i in range(0, len(paper.summary), chunk_size)]
            
            for i, chunk in enumerate(summary_chunks):
                self.chunks.append({
                    'paper_id': paper.paper_id,
                    'title': paper.title,
                    'authors': paper.authors,
                    'arxiv_url': paper.arxiv_url,
                    'pdf_url': paper.pdf_url,
                    'chunk_index': i,
                    'content': chunk
                })
        
        # 使用TF-IDF进行文本相似度计算（简化版本）
        if self.chunks:
            self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
            texts = [chunk['content'] for chunk in self.chunks]
            self.tfidf_matrix = self.vectorizer.fit_transform(texts)
            logger.info(f"向量数据库已更新，包含 {len(self.chunks)} 个chunk")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """在向量数据库中搜索相关chunk"""
        if not hasattr(self, 'tfidf_matrix') or len(self.chunks) == 0:
            return []
            
        # 使用TF-IDF计算相似度
        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        # 获取最相似的top_k个结果
        top_indices = similarities.argsort()[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if idx < len(self.chunks):
                chunk = self.chunks[idx]
                results.append({
                    **chunk,
                    'similarity': similarities[idx]
                })
        
        return results

# 全局向量数据库实例
vector_db = VectorDB()

def call_ollama(messages: List[Dict]) -> str:
    """调用本地Ollama模型"""
    url = f"{OLLAMA_BASE_URL}/api/chat"
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]
    except Exception as e:
        logger.error(f"调用Ollama失败: {e}")
        raise HTTPException(status_code=500, detail=f"模型调用失败: {str(e)}")

def search_arxiv_papers(query: str, max_results: int = 20, sort_by: str = "relevance") -> List[Paper]:
    """搜索ArXiv论文"""
    try:
        # 配置搜索参数
        if sort_by == "date":
            sort_criterion = arxiv.SortCriterion.SubmittedDate
        elif sort_by == "title":
            sort_criterion = arxiv.SortCriterion.Relevance  # Arxiv API不支持按标题排序
        else:
            sort_criterion = arxiv.SortCriterion.Relevance
            
        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=sort_criterion
        )
        
        papers = []
        for result in client.results(search):
            paper = Paper(
                paper_id=result.entry_id.split('/')[-1],
                title=result.title,
                authors=[author.name for author in result.authors],
                summary=result.summary,
                published=result.published.strftime("%Y-%m-%d"),
                updated=result.updated.strftime("%Y-%m-%d") if result.updated else result.published.strftime("%Y-%m-%d"),
                arxiv_url=result.entry_id,
                pdf_url=result.pdf_url
            )
            papers.append(paper)
        
        logger.info(f"从ArXiv搜索到 {len(papers)} 篇论文")
        return papers
        
    except Exception as e:
        logger.error(f"ArXiv搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"论文搜索失败: {str(e)}")

@app.get("/")
async def root():
    return {"message": "ArXiv RAG API 服务运行中", "version": "1.0.0"}

@app.post("/search", response_model=SearchResponse)
async def search_papers(request: SearchRequest):
    """搜索论文接口"""
    try:
        # 搜索论文
        papers = search_arxiv_papers(
            query=request.query,
            max_results=request.max_results,
            sort_by=request.sort_by
        )
        
        # 更新向量数据库
        vector_db.add_papers(papers)
        
        # 分页处理
        start_idx = (request.page - 1) * request.page_size
        end_idx = start_idx + request.page_size
        paginated_papers = papers[start_idx:end_idx]
        
        total_pages = (len(papers) + request.page_size - 1) // request.page_size
        
        return SearchResponse(
            papers=paginated_papers,
            page=request.page,
            total_pages=total_pages,
            total=len(papers)
        )
        
    except Exception as e:
        logger.error(f"搜索接口错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """RAG问答接口"""
    try:
        # 在向量数据库中搜索相关chunk
        relevant_chunks = vector_db.search(request.question, top_k=request.top_k)
        
        if not relevant_chunks:
            raise HTTPException(status_code=404, detail="未找到相关论文内容")
        
        # 构建上下文
        context = "以下是从相关论文中检索到的内容：\n\n"
        for i, chunk in enumerate(relevant_chunks):
            context += f"【论文 {i+1}】{chunk['title']}\n"
            context += f"作者：{', '.join(chunk['authors'])}\n"
            context += f"内容：{chunk['content']}\n\n"
        
        # 构建提示词
        prompt = f"""基于以下论文内容，请回答用户的问题。

论文内容：
{context}

用户问题：{request.question}

请基于上述论文内容提供准确、专业的回答，并注明信息来源。如果论文内容不足以回答问题，请说明情况。"""

        # 调用Ollama模型
        messages = [
            {"role": "system", "content": "你是一个专业的学术助手，基于提供的论文内容回答用户问题。"},
            {"role": "user", "content": prompt}
        ]
        
        answer = call_ollama(messages)
        
        # 构建引用信息
        citations = []
        for chunk in relevant_chunks:
            citation = Citation(
                paper_id=chunk['paper_id'],
                title=chunk['title'],
                authors=chunk['authors'],
                arxiv_url=chunk['arxiv_url'],
                pdf_url=chunk.get('pdf_url'),
                chunk_index=chunk['chunk_index'],
                content=chunk['content'][:200] + "..."  # 截取部分内容
            )
            citations.append(citation)
        
        return AskResponse(
            answer=answer,
            citations=citations
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"问答接口错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """健康检查接口"""
    try:
        # 测试Ollama连接
        test_response = call_ollama([{"role": "user", "content": "你好"}])
        return {
            "status": "healthy",
            "ollama_connection": "ok",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"服务异常: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)