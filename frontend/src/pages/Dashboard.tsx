import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

function MetricCard({ title, value, delta }: { title: string; value: string; delta: string }) {
  const isPositive = delta.trim().startsWith('+')
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm text-muted-foreground">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        <div className={isPositive ? 'text-green-600 mt-1' : 'text-red-600 mt-1'}>{delta}</div>
      </CardContent>
    </Card>
  )
}

export default function Dashboard() {
  return (
    <div className="w-full">
      <h2 className="text-2xl font-semibold mb-2">👋 Welcome to ValueCell !</h2>
      <div className="grid grid-cols-1 gap-2 md:grid-cols-2 lg:grid-cols-3">
        <MetricCard title="NASDAQ" value="$23355.78" delta="-478.94 -2.01%" />
        <MetricCard title="HSI" value="$25974.63" delta="+22.23 +0.09%" />
        <MetricCard title="SSE" value="$11.53" delta="-0.00 -NaN%" />
      </div>
    </div>
  )
}


