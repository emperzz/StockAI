import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

interface Sector {
  id: string
  name: string
  stocks: string[]
}

export default function Sectors() {
  const [sectors, setSectors] = useState<Sector[]>([])
  const [name, setName] = useState('')
  const [stocksText, setStocksText] = useState('')

  const addSector = () => {
    const trimmedName = name.trim()
    if (!trimmedName) return
    const stocks = stocksText
      .split(/[\n,，]/)
      .map((s) => s.trim())
      .filter(Boolean)

    const newSector: Sector = {
      id: `${Date.now()}`,
      name: trimmedName,
      stocks,
    }
    setSectors((prev) => [newSector, ...prev])
    setName('')
    setStocksText('')
  }

  return (
    <div className="w-full space-y-4">
      <h2 className="text-2xl font-semibold">板块管理</h2>

      <Card>
        <CardHeader>
          <CardTitle>新增板块</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            <Input
              placeholder="板块名称，如：新能源、半导体"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
            <Button onClick={addSector}>添加</Button>
          </div>
          <textarea
            className="w-full min-h-[120px] resize-y rounded-md border bg-white p-2 text-sm"
            placeholder="股票代码清单，逗号或换行分隔，如：SSE:600036, SZSE:000001"
            value={stocksText}
            onChange={(e) => setStocksText(e.target.value)}
          />
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {sectors.map((s) => (
          <Card key={s.id}>
            <CardHeader>
              <CardTitle className="text-base">{s.name}</CardTitle>
            </CardHeader>
            <CardContent>
              {s.stocks.length === 0 ? (
                <div className="text-sm text-muted-foreground">无股票</div>
              ) : (
                <ul className="text-sm list-disc pl-4">
                  {s.stocks.map((code, idx) => (
                    <li key={idx}>{code}</li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}


