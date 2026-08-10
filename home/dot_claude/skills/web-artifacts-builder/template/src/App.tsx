import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

export default function App() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-14">
      <Badge variant="secondary" className="font-mono">artifact</Badge>
      <h1 className="mt-3 text-4xl font-semibold tracking-tight">New artifact</h1>
      <p className="mt-3 text-lg text-muted-foreground">Edit <code>src/App.tsx</code>, then build.</p>
      <Card className="mt-8"><CardHeader><CardTitle>Ready</CardTitle></CardHeader>
        <CardContent className="text-sm text-muted-foreground">shadcn/ui + Tailwind + Vite single-file, deps pre-installed.</CardContent></Card>
    </main>
  )
}
