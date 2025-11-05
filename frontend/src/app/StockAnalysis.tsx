import { useState } from 'react'
import { useAnalyzeStock } from '@/api/stock'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import ReactMarkdown from 'react-markdown'
import { Search, Loader2 } from 'lucide-react'
import StockChart from '@/components/StockChart'
import StockDataTable from '@/components/StockDataTable'

export default function StockAnalysis() {
  const [stockCode, setStockCode] = useState('SZSE:000001')
  const [interval, setInterval] = useState<'1d' | '1m'>('1d')
  const analyzeMutation = useAnalyzeStock()

  const handleAnalyze = () => {
    if (!stockCode.trim()) return
    analyzeMutation.mutate({
      stock_code: stockCode.trim(),
      interval,
    })
  }

  return (
    <div className="space-y-4">
      {/* 输入区域 */}
      <Card>
        <CardHeader>
          <CardTitle>📝 输入股票代码</CardTitle>
          <CardDescription>支持多只，用逗号分隔。例如: SZSE:000001,SSE:600036</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              placeholder="股票代码"
              value={stockCode}
              onChange={(e) => setStockCode(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  handleAnalyze()
                }
              }}
            />
            <Select
              value={interval}
              onChange={(e) => setInterval(e.target.value as '1d' | '1m')}
              className="w-32"
            >
              <option value="1d">日线</option>
              <option value="1m">分钟线</option>
            </Select>
            <Button
              onClick={handleAnalyze}
              disabled={analyzeMutation.isPending || !stockCode.trim()}
            >
              {analyzeMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  分析中...
                </>
              ) : (
                <>
                  <Search className="mr-2 h-4 w-4" />
                  分析股票
                </>
              )}
            </Button>
          </div>

          <div className="text-sm text-muted-foreground">
            <p>💡 使用说明</p>
            <ul className="list-disc list-inside space-y-1 mt-2">
              <li>输入6位股票代码（如：000001）</li>
              <li>点击"分析股票"按钮</li>
              <li>查看分析结果和图表</li>
            </ul>
            <p className="mt-2">📋 示例代码</p>
            <ul className="list-disc list-inside space-y-1 mt-2">
              <li>000001: 平安银行</li>
              <li>000002: 万科A</li>
              <li>600000: 浦发银行</li>
              <li>600036: 招商银行</li>
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* 分析结果 */}
      {analyzeMutation.data && (
        <>
          <Card>
            <CardHeader>
              <CardTitle>📊 分析结果</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="prose prose-sm max-w-none dark:prose-invert">
                <ReactMarkdown>{analyzeMutation.data.analysis_text}</ReactMarkdown>
              </div>
            </CardContent>
          </Card>

          {/* 数据表格 */}
          {analyzeMutation.data.data_table && analyzeMutation.data.data_table.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>📋 股票数据</CardTitle>
              </CardHeader>
              <CardContent>
                <StockDataTable data={analyzeMutation.data.data_table} />
              </CardContent>
            </Card>
          )}

          {/* 图表 */}
          {analyzeMutation.data.chart_data && (
            <Card>
              <CardHeader>
                <CardTitle>📈 K线图</CardTitle>
              </CardHeader>
              <CardContent>
                <StockChart data={analyzeMutation.data.chart_data} />
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* 错误提示 */}
      {analyzeMutation.isError && (
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <p className="text-destructive">
              分析失败: {analyzeMutation.error instanceof Error ? analyzeMutation.error.message : '未知错误'}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

