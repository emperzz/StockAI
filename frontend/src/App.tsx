import { useState } from 'react'
import ChatAssistant from './app/ChatAssistant'

// 中间内容页
import Dashboard from './pages/Dashboard'
import Sectors from './pages/Sectors'

type PageKey = 'dashboard' | 'sectors'

function App() {
  const [activePage, setActivePage] = useState<PageKey>('dashboard')
  const [isSheetOpen, setIsSheetOpen] = useState(false)

  const renderPage = () => {
    if (activePage === 'sectors') return <Sectors />
    return <Dashboard />
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="flex h-screen w-full overflow-hidden">
        {/* 侧边导航 */}
        <aside className="px-4 pt-5 pb-3 w-16 shrink-0 bg-white border-r">
          <div className="flex flex-col items-center gap-3">
            {/* 返回 Dashboard 放最上 */}
            <button
              type="button"
              aria-label="Dashboard"
              data-active={activePage === 'dashboard'}
              onClick={() => setActivePage('dashboard')}
              className="box-border flex size-10 items-center justify-center rounded-full cursor-pointer transition-all text-gray-700 hover:data-[active=false]:bg-neutral-300 data-[active=true]:bg-black data-[active=true]:text-white"
            >
              D
            </button>
            {/* Market 按钮 -> 板块管理 */}
            <button
              type="button"
              aria-label="Market"
              data-active={activePage === 'sectors'}
              onClick={() => setActivePage('sectors')}
              className="box-border flex size-10 items-center justify-center rounded-full cursor-pointer transition-all text-gray-700 hover:data-[active=false]:bg-neutral-300 data-[active=true]:bg-black data-[active=true]:text-white"
            >
              M
            </button>
            {/* 第二个按钮：打开会话列表抽屉 */}
            <button
              type="button"
              aria-label="Market-2"
              data-active={false}
              onClick={() => setIsSheetOpen(true)}
              className="box-border flex size-10 items-center justify-center rounded-full cursor-pointer transition-all text-gray-700 hover:data-[active=false]:bg-neutral-300 data-[active=true]:bg-black data-[active=true]:text-white"
            >
              M2
            </button>
          </div>
        </aside>

        {/* 中间内容，仅保留指数网格或板块管理页面 */}
        <main className="flex flex-1 flex-col gap-4 overflow-hidden bg-gray-100 py-4 pr-4 pl-2">
          {renderPage()}
        </main>

        {/* 右侧常驻 AI 会话窗口 */}
        <section className="w-full max-w-md shrink-0 bg-transparent">
          <div className="h-full pr-2 py-4">
            <ChatAssistant />
          </div>
        </section>

        {/* 会话列表抽屉 */}
        {isSheetOpen && (
          <div className="fixed inset-0 z-50">
            <div className="absolute inset-0 bg-black/30" onClick={() => setIsSheetOpen(false)} />
            <div className="absolute right-0 top-0 h-full w-[360px] bg-white shadow-xl flex flex-col">
              <div data-slot="sheet-header" className="flex flex-col gap-1.5 p-4 border-b">
                Conversation List
              </div>
              <div className="flex-1 overflow-auto p-4 space-y-2">
                <div>Conversation conv-a8bfae61ec34491ab90413a00bb7c8d3 2025/10/28</div>
              </div>
              <section className="flex flex-1 flex-col items-center p-4 border-t">
                ValueCell Agent valuecell super-agent 你好
              </section>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App

