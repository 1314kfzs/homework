import React, { useState, useEffect, useRef } from 'react'
import './index.css'

// 数学公式渲染函数
const renderMath = (text) => {
  if (!text) return text;
  
  // 简单的LaTeX数学公式检测和渲染
  const mathRegex = /\$(.*?)\$/g;
  let result = text;
  let mathElements = [];
  
  // 提取数学公式
  let match;
  let index = 0;
  while ((match = mathRegex.exec(text)) !== null) {
    const mathContent = match[1];
    const mathId = `math-${index++}`;
    mathElements.push({ id: mathId, content: mathContent });
    result = result.replace(match[0], `<span id="${mathId}"></span>`);
  }
  
  // 延迟渲染数学公式（等待DOM更新后）
  setTimeout(() => {
    mathElements.forEach(({ id, content }) => {
      const element = document.getElementById(id);
      if (element) {
        try {
          window.katex.render(content, element, {
            throwOnError: false,
            displayMode: content.includes('\\displaystyle') || content.includes('\\['),
          });
        } catch (error) {
          console.error('KaTeX渲染错误:', error);
          element.textContent = `$${content}$`;
        }
      }
    });
  }, 100);
  
  return { __html: result };
};

// 数学公式渲染组件
const MathText = ({ children }) => {
  return <div dangerouslySetInnerHTML={renderMath(children)} />;
};

const API_BASE = import.meta.env.VITE_LOCAL_API_BASE || 'http://172.27.144.1:8001'

export default function App() {
  const [query, setQuery] = useState('')
  const [papers, setPapers] = useState([])
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [citations, setCitations] = useState([])
  const [loadingSearch, setLoadingSearch] = useState(false)
  const [loadingAsk, setLoadingAsk] = useState(false)
  const [error, setError] = useState('')
  const [backendStatus, setBackendStatus] = useState('checking')
  
  // 分页状态
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage, setItemsPerPage] = useState(5)
  const [totalPages, setTotalPages] = useState(1)
  const [totalPapers, setTotalPapers] = useState(0)

  // 防抖定时器引用
  const searchTimeoutRef = useRef(null)

  // 检查后端连接状态
  useEffect(() => {
    const checkBackendStatus = async () => {
      try {
        // 尝试访问一个实际存在的API端点，比如/search或/ask
        const res = await fetch(`${API_BASE}/search`, { 
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: 'test' })
        })
        // 即使返回错误状态码（如400），只要连接成功就认为在线
        setBackendStatus('online')
      } catch {
        setBackendStatus('offline')
      }
    }
    
    checkBackendStatus()
    const interval = setInterval(checkBackendStatus, 30000) // 每30秒检查一次
    return () => clearInterval(interval)
  }, [])

  // 清理防抖定时器
  useEffect(() => {
    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current)
      }
    }
  }, [])

  const handleSearchWithPage = async (page, pageSize) => {
    setLoadingSearch(true)
    setError('')
    try {
      const res = await fetch(`${API_BASE}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          query,
          max_results: 20,
          sort_by: 'relevance',
          page: page,
          page_size: pageSize
        })
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setPapers(data.papers)
      setCurrentPage(data.page)
      setTotalPages(data.total_pages)
      setTotalPapers(data.total)
    } catch (e) {
      setError(String(e))
    } finally {
      setLoadingSearch(false)
    }
  }

  // 防抖搜索函数
  const handleSearchInputChange = (value) => {
    setQuery(value)
    
    // 清除之前的定时器
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current)
    }
    
    // 如果输入为空，不进行搜索
    if (!value.trim()) {
      setPapers([])
      return
    }
    
    // 设置新的定时器，500ms后执行搜索
    searchTimeoutRef.current = setTimeout(() => {
      handleSearchWithPage(1, itemsPerPage)
    }, 500)
  }

  const handleSearch = async () => {
    // 清除防抖定时器，立即执行搜索
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current)
    }
    await handleSearchWithPage(1, itemsPerPage)
  }

  const handleAsk = async () => {
    setLoadingAsk(true)
    setError('')
    setAnswer('')
    setCitations([])
    try {
      const res = await fetch(`${API_BASE}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, question, max_results: 5, top_k: 5 })
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setAnswer(data.answer)
      setCitations(data.citations || [])
    } catch (e) {
      setError(String(e))
    } finally {
      setLoadingAsk(false)
    }
  }

  // 骨架屏组件
  const SkeletonLoader = () => (
    <div className="skeleton-container">
      {[...Array(3)].map((_, index) => (
        <div key={index} className="skeleton-item">
          <div className="skeleton-line long"></div>
          <div className="skeleton-line medium"></div>
          <div className="skeleton-line short"></div>
          <div className="skeleton-line long"></div>
        </div>
      ))}
    </div>
  )

  // 分页计算 - 现在由后端处理分页
  const currentPapers = papers

  return (
    <div className="app-container">
      <div className="app-header">
        <h1 className="app-title">ArXiv 论文搜索与问答</h1>
        <p className="app-subtitle">
          基于本地 Qwen RAG 系统
          <span className={`status-indicator ${backendStatus === 'online' ? 'status-online' : 'status-offline'}`}>
            {backendStatus === 'online' ? '✓ 后端在线' : '✗ 后端离线'}
          </span>
        </p>
      </div>

      <div className="main-content">
        <div className="search-section">
          <h2 className="section-title">1. 搜索论文</h2>
        


        <div className="search-container">
          <input
            className="search-input"
            value={query}
            onChange={(e) => handleSearchInputChange(e.target.value)}
            placeholder="输入主题关键词，例如：Graph Neural Networks, Machine Learning..."
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button 
            className="btn btn-primary" 
            onClick={handleSearch} 
            disabled={loadingSearch || !query.trim()}
          >
            {loadingSearch ? <span className="loading">搜索中</span> : '🔍 搜索论文'}
          </button>
        </div>
        
        {error && <div className="error-message">错误：{error}</div>}
        
        {/* 分页信息 */}
        {papers.length > 0 && (
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center', 
            margin: '16px 0',
            padding: '12px',
            background: 'white',
            borderRadius: '8px',
            border: '1px solid #e9ecef'
          }}>
            <div>
              共 {totalPapers} 篇论文，第 {currentPage} 页 / 共 {totalPages} 页
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span>每页显示：</span>
              <select 
                value={itemsPerPage}
                onChange={async (e) => {
                  const newPageSize = parseInt(e.target.value)
                  setItemsPerPage(newPageSize)
                  setCurrentPage(1)
                  // 重新搜索以获取新的分页数据
                  await handleSearchWithPage(1, newPageSize)
                }}
                style={{ padding: '4px 8px', borderRadius: '4px', border: '1px solid #ddd' }}
              >
                <option value={5}>5</option>
                <option value={10}>10</option>
                <option value={20}>20</option>
              </select>
            </div>
          </div>
        )}
        
        <div className="papers-list">
          {loadingSearch ? (
            <SkeletonLoader />
          ) : (
            currentPapers.map((p) => (
              <div key={p.paper_id} className="paper-item">
                <h3 className="paper-title">{p.title}</h3>
                <div className="paper-authors">作者：{p.authors.join(', ')}</div>
                <div className="paper-meta">发布：{p.published} | 更新：{p.updated}</div>
                <div className="paper-links">
                  <a href={p.arxiv_url} target="_blank" rel="noreferrer" className="paper-link">📄 arXiv 页面</a>
                  {p.pdf_url && <a href={p.pdf_url} target="_blank" rel="noreferrer" className="paper-link">📥 下载 PDF</a>}
                </div>
                <p className="paper-summary">{p.summary}</p>
              </div>
            ))
          )}
        </div>

        {/* 分页控件 */}
        {papers.length > 0 && (
          <div style={{ 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center', 
            gap: '8px',
            marginTop: '20px',
            padding: '16px',
            background: 'white',
            borderRadius: '8px',
            border: '1px solid #e9ecef'
          }}>
            <button 
              className="btn btn-secondary"
              onClick={async () => await handleSearchWithPage(currentPage - 1, itemsPerPage)}
              disabled={currentPage === 1}
              style={{ padding: '8px 12px' }}
            >
              上一页
            </button>
            
            <button 
              className="btn btn-secondary"
              onClick={async () => await handleSearchWithPage(currentPage + 1, itemsPerPage)}
              disabled={currentPage >= totalPages}
              style={{ padding: '8px 12px' }}
            >
              下一页
            </button>
            
            <span style={{ marginLeft: '12px', color: '#666' }}>
              第 {currentPage} 页 / 共 {totalPages} 页
            </span>
          </div>
        )}
        </div>

        <div className="sidebar-section">
          <div className="sidebar-content">
            <h2 className="section-title">2. 智能问答（RAG）</h2>
            <p style={{ color: '#666', marginBottom: '16px' }}>
              基于所检索主题的论文临时索引进行问答，并返回引用来源。
            </p>
            
            <textarea
              className="question-textarea"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="输入你的问题，例如：请总结近期在GNN上的对比学习方法关键结论..."
            />
            
            <div>
              <button 
                className="btn btn-primary" 
                onClick={handleAsk} 
                disabled={loadingAsk || !query || !question}
              >
                {loadingAsk ? <span className="loading">思考中</span> : '🤖 向本地 Qwen 询问'}
              </button>
            </div>
            
            {loadingAsk ? (
              <div className="skeleton-container">
                <div className="skeleton-item">
                  <div className="skeleton-line long"></div>
                  <div className="skeleton-line long"></div>
                  <div className="skeleton-line medium"></div>
                </div>
              </div>
            ) : (
              <>
                {answer && (
                  <div className="answer-container">
                    <h3 className="answer-title">📝 AI 回答</h3>
                    <div className="answer-content">
                      <MathText>{answer}</MathText>
                    </div>
                  </div>
                )}
                
                {citations.length > 0 && (
                  <div className="citations-container">
                    <h3 style={{ fontSize: '1.2rem', fontWeight: '600', color: '#495057', marginBottom: '16px' }}>
                      📚 引用来源（Top-k 检索结果）
                    </h3>
                    <div>
                      {citations.map((c, idx) => (
                        <div key={`${c.paper_id}-${c.chunk_index}-${idx}`} className="citation-item">
                          <h4 style={{ fontSize: '1rem', fontWeight: '600', color: '#495057', marginBottom: '8px' }}>
                            {c.title}
                          </h4>
                          <div style={{ fontSize: '0.9rem', color: '#6c757d', marginBottom: '8px' }}>
                            作者：{Array.isArray(c.authors) ? c.authors.join(', ') : c.authors}
                          </div>
                          <div>
                            <a href={c.arxiv_url} target="_blank" rel="noreferrer" className="paper-link">查看论文</a>
                            {c.pdf_url && <a href={c.pdf_url} target="_blank" rel="noreferrer" className="paper-link">下载 PDF</a>}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}