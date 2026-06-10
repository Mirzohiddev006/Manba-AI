import { useQuery } from '@tanstack/react-query';

import { adminFetch } from '@/shared/api/client';
import { Badge, Card, CardTitle, Table } from '@/shared/ui';

interface Monitoring {
  recent_calls: { model: string; in: number; out: number; cost_usd: number;
    latency_ms: number; at: string }[];
  low_confidence: { id: number; raw: string; confidence: number; type: string }[];
}

export function AiMonitoringPage() {
  const { data } = useQuery({
    queryKey: ['ai-monitoring'],
    queryFn: () => adminFetch<Monitoring>('/api/v1/admin/ai-monitoring'),
    refetchInterval: 30_000,
  });
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">AI monitoring</h1>
      <Card>
        <CardTitle>Past ishonchli tahlillar (korpusga nomzodlar)</CardTitle>
        <Table headers={['Kirish', 'Tur', 'Ishonch']}>
          {data?.low_confidence.map((s) => (
            <tr key={s.id}>
              <td className="max-w-md truncate px-4 py-2">{s.raw}</td>
              <td className="px-4 py-2"><Badge color="blue">{s.type}</Badge></td>
              <td className="px-4 py-2">
                <Badge color={s.confidence < 0.4 ? 'red' : 'amber'}>
                  {Math.round(s.confidence * 100)}%
                </Badge>
              </td>
            </tr>
          ))}
        </Table>
      </Card>
      <Card>
        <CardTitle>LLM so'rovlar jurnali</CardTitle>
        <Table headers={['Model', 'Token (in/out)', 'Narx', 'Latency', 'Vaqt']}>
          {data?.recent_calls.map((c, i) => (
            <tr key={i}>
              <td className="px-4 py-2">{c.model}</td>
              <td className="px-4 py-2">{c.in} / {c.out}</td>
              <td className="px-4 py-2">${c.cost_usd.toFixed(4)}</td>
              <td className="px-4 py-2">{c.latency_ms} ms</td>
              <td className="px-4 py-2 text-gray-500">{new Date(c.at).toLocaleString()}</td>
            </tr>
          ))}
        </Table>
      </Card>
    </div>
  );
}
