import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useMemo } from 'react'
import { useGetQuotes } from '@/api/stock'

function MetricCard({ title, value, delta }: { title: string; value: string; delta: string }) {
  const trimmed = delta.trim()
  const isPositive = trimmed.startsWith('+')
  const isNegative = trimmed.startsWith('-')
  const colorClass = isPositive ? 'text-red-600 mt-1' : isNegative ? 'text-green-600 mt-1' : 'text-gray-500 mt-1'
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm text-muted-foreground">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        <div className={colorClass}>{delta}</div>
      </CardContent>
    </Card>
  )
}

export default function Dashboard() {
  const tickers = ['SSE:000001', 'SZSE:399001', 'SZSE:399006']
  const { data: quotes } = useGetQuotes(tickers)

  const sse = useMemo(() => {
    const list = quotes ?? []
    const item = list.find((x) => x.code === '000001')
    if (!item) return { value: '--', delta: '--' }
    const sign = item.change >= 0 ? '+' : ''
    return {
      value: `$${(item.price ?? 0).toFixed(2)}`,
      delta: `${sign}${(item.change ?? 0).toFixed(2)} ${sign}${(item.pct ?? 0).toFixed(2)}%`,
    }
  }, [quotes])

  const sz = useMemo(() => {
    const list = quotes ?? []
    const item = list.find((x) => x.code === '399001')
    if (!item) return { value: '--', delta: '--' }
    const sign = item.change >= 0 ? '+' : ''
    return {
      value: `$${(item.price ?? 0).toFixed(2)}`,
      delta: `${sign}${(item.change ?? 0).toFixed(2)} ${sign}${(item.pct ?? 0).toFixed(2)}%`,
    }
  }, [quotes])

  const cy = useMemo(() => {
    const list = quotes ?? []
    const item = list.find((x) => x.code === '399006')
    if (!item) return { value: '--', delta: '--' }
    const sign = item.change >= 0 ? '+' : ''
    return {
      value: `$${(item.price ?? 0).toFixed(2)}`,
      delta: `${sign}${(item.change ?? 0).toFixed(2)} ${sign}${(item.pct ?? 0).toFixed(2)}%`,
    }
  }, [quotes])

  // 指数实时行情使用上方 quotes 计算得到

  return (
    <div className="w-full">
      <h2 className="text-2xl font-semibold mb-2">👋 Welcome to ValueCell !</h2>
      <div className="grid grid-cols-1 gap-2 md:grid-cols-2 lg:grid-cols-3">
        <MetricCard title="上证指数" value={sse.value} delta={sse.delta} />
        <MetricCard title="深证成指" value={sz.value} delta={sz.delta} />
        <MetricCard title="创业板指" value={cy.value} delta={cy.delta} />
      </div>
    </div>
  )
}


