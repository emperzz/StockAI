import { useState } from 'react'
import StockAnalysis from './app/StockAnalysis'
import ChatAssistant from './app/ChatAssistant'

function App() {
  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto p-4">
        <header className="mb-6">
          <h1 className="text-3xl font-bold text-foreground">
            🚀 StockAI - 中国股市AI分析系统
          </h1>
        </header>
        
        <div className="grid grid-cols-12 gap-4">
          {/* 左侧：股票分析区域 (占 8 列) */}
          <div className="col-span-12 lg:col-span-8">
            <StockAnalysis />
          </div>
          
          {/* 右侧：对话助手区域 (占 4 列) */}
          <div className="col-span-12 lg:col-span-4">
            <ChatAssistant />
          </div>
        </div>
      </div>
    </div>
  )
}

export default App

