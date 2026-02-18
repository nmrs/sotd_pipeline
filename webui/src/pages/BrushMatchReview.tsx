import React, { useCallback, useEffect, useState } from 'react';

const API = '/api/brush-match';

interface RunInfo {
  run_id: string;
  path: string;
}

interface QueueItem {
  entry_id: string;
  raw: string;
  norm: string;
  decision_type: string;
}

interface QueueResponse {
  run_id: string;
  status: string;
  items: QueueItem[];
  total: number;
}

interface Candidate {
  entity_type: string;
  entity_id: string | null;
  name: string;
  score: number;
  explanation?: { brand?: string; model?: string };
}

interface EntryData {
  run_id?: string;
  entry_id?: string;
  raw: string;
  norm: string;
  tokens?: string[];
  kind_result?: { kind_pred?: string; confidence?: number; margin?: number };
  segmentation_result?: {
    knot_span?: [number, number];
    handle_chunk?: string;
    knot_chunk?: string;
  };
  candidates?: {
    complete_candidates?: Candidate[];
    handle_candidates?: Candidate[];
    knot_candidates?: Candidate[];
  };
  decision?: { decision_type?: string };
  resolved_v2?: {
    source?: string;
    brush?: { brand?: string; model?: string };
    composite?: boolean;
    handle?: { brand?: string; model?: string };
    knot?: { brand?: string; model?: string };
  };
}

type QueueStatus = 'needs_review' | 'auto_accept';

export default function BrushMatchReview() {
  const [runs, setRuns] = useState<RunInfo[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string>('');
  const [queueStatus, setQueueStatus] = useState<QueueStatus>('needs_review');
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [queueLoading, setQueueLoading] = useState(false);
  const [selectedEntryId, setSelectedEntryId] = useState<string | null>(null);
  const [entry, setEntry] = useState<EntryData | null>(null);
  const [entryLoading, setEntryLoading] = useState(false);
  const [acceptSelection, setAcceptSelection] = useState<
    | { brush: { brand: string; model: string } }
    | { handle: { brand: string; model: string }; knot: { brand: string; model: string } }
    | null
  >(null);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const fetchRuns = useCallback(async () => {
    try {
      const res = await fetch(`${API}/runs`);
      const data = await res.json();
      setRuns(Array.isArray(data) ? data : []);
      if (Array.isArray(data) && data.length > 0 && !selectedRunId) {
        setSelectedRunId(data[0].run_id);
      }
    } catch (e) {
      setRuns([]);
    }
  }, [selectedRunId]);

  useEffect(() => {
    fetchRuns();
  }, [fetchRuns]);

  const fetchQueue = useCallback(async () => {
    if (!selectedRunId) {
      setQueue([]);
      return;
    }
    setQueueLoading(true);
    try {
      const res = await fetch(
        `${API}/queue?run_id=${encodeURIComponent(selectedRunId)}&status=${queueStatus}&limit=100`
      );
      const data: QueueResponse = await res.json();
      setQueue(data.items || []);
    } catch (e) {
      setQueue([]);
    } finally {
      setQueueLoading(false);
    }
  }, [selectedRunId, queueStatus]);

  useEffect(() => {
    fetchQueue();
  }, [fetchQueue]);

  const fetchEntry = useCallback(async (entryId: string) => {
    setSelectedEntryId(entryId);
    setEntry(null);
    setAcceptSelection(null);
    setEntryLoading(true);
    try {
      const res = await fetch(`${API}/entry/${encodeURIComponent(entryId)}`);
      if (!res.ok) {
        setEntry(null);
        return;
      }
      const data: EntryData = await res.json();
      setEntry(data);
      const kr = data.kind_result;
      const cand = data.candidates;
      if (kr?.kind_pred === 'complete' && cand?.complete_candidates?.length) {
        const top = cand.complete_candidates[0];
        const brand = top.explanation?.brand ?? '';
        const model = top.explanation?.model ?? '';
        setAcceptSelection({ brush: { brand, model } });
      } else if (
        (kr?.kind_pred === 'composite' || kr?.kind_pred === 'unknown') &&
        cand?.handle_candidates?.length &&
        cand?.knot_candidates?.length
      ) {
        const h = cand.handle_candidates[0];
        const k = cand.knot_candidates[0];
        setAcceptSelection({
          handle: {
            brand: h.explanation?.brand ?? '',
            model: h.explanation?.model ?? '',
          },
          knot: {
            brand: k.explanation?.brand ?? '',
            model: k.explanation?.model ?? '',
          },
        });
      } else {
        setAcceptSelection(null);
      }
    } catch (e) {
      setEntry(null);
    } finally {
      setEntryLoading(false);
    }
  }, []);

  const submitDecision = async () => {
    if (!selectedEntryId || !acceptSelection) return;
    setSubmitting(true);
    setMessage(null);
    try {
      const res = await fetch(`${API}/entry/${encodeURIComponent(selectedEntryId)}/decision`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          selection: acceptSelection,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setMessage({ type: 'error', text: data.detail || data.message || 'Failed' });
        return;
      }
      setMessage({ type: 'success', text: data.message || 'Accepted and saved.' });
      setEntry(null);
      setSelectedEntryId(null);
      fetchQueue();
    } catch (e) {
      setMessage({ type: 'error', text: String(e) });
    } finally {
      setSubmitting(false);
    }
  };

  const kindPred = entry?.kind_result?.kind_pred ?? 'unknown';
  const seg = entry?.segmentation_result;
  const knotSpan = seg?.knot_span ?? [0, 0];
  const tokens = entry?.tokens ?? [];
  const cand = entry?.candidates;
  const isAutoAccept = entry?.decision?.decision_type === 'auto_accept';

  function formatAutoMatched(ent: EntryData | null): string | null {
    if (!ent) return null;
    const rv = ent.resolved_v2;
    if (rv?.brush) {
      const b = rv.brush;
      return [b.brand ?? '', b.model ?? ''].filter(Boolean).join(' ').trim() || null;
    }
    if (rv?.composite && rv?.handle && rv?.knot) {
      const h = [rv.handle.brand ?? '', rv.handle.model ?? ''].filter(Boolean).join(' ').trim();
      const k = [rv.knot.brand ?? '', rv.knot.model ?? ''].filter(Boolean).join(' ').trim();
      return `Handle: ${h || '—'} / Knot: ${k || '—'}`;
    }
    const kr = ent.kind_result;
    const c = ent.candidates;
    if (kr?.kind_pred === 'complete' && c?.complete_candidates?.length) {
      const top = c.complete_candidates[0];
      const brand = top.explanation?.brand ?? '';
      const model = top.explanation?.model ?? '';
      return [brand, model].filter(Boolean).join(' ').trim() || null;
    }
    if (c?.handle_candidates?.length && c?.knot_candidates?.length) {
      const h = c.handle_candidates[0];
      const k = c.knot_candidates[0];
      const hStr = [h.explanation?.brand ?? '', h.explanation?.model ?? ''].filter(Boolean).join(' ').trim();
      const kStr = [k.explanation?.brand ?? '', k.explanation?.model ?? ''].filter(Boolean).join(' ').trim();
      return `Handle: ${hStr || '—'} / Knot: ${kStr || '—'}`;
    }
    return null;
  }

  const autoMatchedLabel = isAutoAccept ? formatAutoMatched(entry) : null;

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Brush Match Review (v2)</h1>
        <p className="text-gray-600 mb-4">
          Review v2 brush-match entries that need confirmation. Accept writes to correct_matches and
          gold labels.
        </p>

        <div className="flex flex-wrap gap-4 items-center mb-4">
          <label className="font-medium">Run</label>
          <select
            className="border rounded px-2 py-1"
            value={selectedRunId}
            onChange={e => {
              setSelectedRunId(e.target.value);
              setSelectedEntryId(null);
              setEntry(null);
            }}
          >
            <option value="">Select run</option>
            {runs.map(r => (
              <option key={r.run_id} value={r.run_id}>
                {r.run_id}
              </option>
            ))}
          </select>
          <div className="flex gap-2">
            <button
              type="button"
              className={`px-3 py-1 rounded ${queueStatus === 'needs_review' ? 'bg-blue-200' : 'bg-gray-200 hover:bg-gray-300'}`}
              onClick={() => {
                setQueueStatus('needs_review');
                setSelectedEntryId(null);
                setEntry(null);
              }}
            >
              Needs review
            </button>
            <button
              type="button"
              className={`px-3 py-1 rounded ${queueStatus === 'auto_accept' ? 'bg-blue-200' : 'bg-gray-200 hover:bg-gray-300'}`}
              onClick={() => {
                setQueueStatus('auto_accept');
                setSelectedEntryId(null);
                setEntry(null);
              }}
            >
              Auto-accepted
            </button>
          </div>
          <button
            type="button"
            className="bg-gray-200 hover:bg-gray-300 rounded px-3 py-1"
            onClick={fetchQueue}
          >
            Refresh queue
          </button>
          <span className="text-sm text-gray-500">
            {queue.length} {queueStatus === 'needs_review' ? 'needs_review' : 'auto-accepted'}
          </span>
        </div>

        {message && (
          <div
            className={`mb-4 p-2 rounded ${message.type === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}
          >
            {message.text}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="border rounded bg-white p-4">
            <h2 className="font-semibold mb-2">Queue</h2>
            {queueLoading ? (
              <p className="text-gray-500">Loading…</p>
            ) : queue.length === 0 ? (
              <p className="text-gray-500">No items or select a run.</p>
            ) : (
              <ul className="space-y-1 max-h-96 overflow-y-auto">
                {queue.map(item => (
                  <li key={item.entry_id}>
                    <button
                      type="button"
                      className={`text-left w-full px-2 py-1 rounded truncate block ${selectedEntryId === item.entry_id ? 'bg-blue-100' : 'hover:bg-gray-100'}`}
                      onClick={() => fetchEntry(item.entry_id)}
                    >
                      {item.raw || item.norm}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="border rounded bg-white p-4">
            <h2 className="font-semibold mb-2">Entry detail</h2>
            {entryLoading ? (
              <p className="text-gray-500">Loading…</p>
            ) : !entry ? (
              <p className="text-gray-500">Select an entry from the queue.</p>
            ) : (
              <div className="space-y-3 text-sm">
                <div>
                  <span className="font-medium">Raw:</span>{' '}
                  <span className="text-gray-700">{entry.raw}</span>
                </div>
                <div>
                  <span className="font-medium">Norm:</span>{' '}
                  <span className="text-gray-600">{entry.norm}</span>
                </div>
                <div>
                  <span className="font-medium">Kind:</span>{' '}
                  <span className="text-gray-700">{kindPred}</span>
                </div>
                {isAutoAccept && (
                  <div className="p-2 bg-amber-50 rounded border border-amber-200">
                    <span className="font-medium">Auto-matched to:</span>{' '}
                    <span className="text-gray-800">{autoMatchedLabel ?? '—'}</span>
                    {entry?.kind_result?.confidence != null && (
                      <span className="ml-2 text-gray-600">
                        (confidence {entry.kind_result.confidence.toFixed(2)}
                        {entry.kind_result.margin != null ? `, margin ${entry.kind_result.margin.toFixed(2)}` : ''})
                      </span>
                    )}
                  </div>
                )}
                {tokens.length > 0 && (
                  <div>
                    <span className="font-medium">Tokens (knot span [{knotSpan[0]}, {knotSpan[1]}]):</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {tokens.map((t, i) => (
                        <span
                          key={i}
                          className={`px-1 rounded ${i >= knotSpan[0] && i < knotSpan[1] ? 'bg-amber-200' : 'bg-gray-100'}`}
                        >
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {seg?.handle_chunk != null && (
                  <div>
                    <span className="font-medium">Handle chunk:</span>{' '}
                    <span className="text-gray-600">{seg.handle_chunk}</span>
                  </div>
                )}
                {seg?.knot_chunk != null && (
                  <div>
                    <span className="font-medium">Knot chunk:</span>{' '}
                    <span className="text-gray-600">{seg.knot_chunk}</span>
                  </div>
                )}

                {cand?.complete_candidates && cand.complete_candidates.length > 0 && (
                  <div>
                    <span className="font-medium">Complete candidates</span>
                    <ul className="list-disc list-inside mt-1">
                      {cand.complete_candidates.slice(0, 5).map((c, i) => (
                        <li key={i}>
                          {c.name} ({(c.explanation?.brand ?? '')} / {(c.explanation?.model ?? '')}) — {c.score.toFixed(2)}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {cand?.handle_candidates && cand.handle_candidates.length > 0 && (
                  <div>
                    <span className="font-medium">Handle candidates</span>
                    <ul className="list-disc list-inside mt-1">
                      {cand.handle_candidates.slice(0, 5).map((c, i) => (
                        <li key={i}>
                          {c.name} — {c.score.toFixed(2)}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {cand?.knot_candidates && cand.knot_candidates.length > 0 && (
                  <div>
                    <span className="font-medium">Knot candidates</span>
                    <ul className="list-disc list-inside mt-1">
                      {cand.knot_candidates.slice(0, 5).map((c, i) => (
                        <li key={i}>
                          {c.name} — {c.score.toFixed(2)}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {acceptSelection && !isAutoAccept && queueStatus === 'needs_review' && (
                  <div className="pt-2 border-t">
                    <span className="font-medium">Accept as:</span>
                    <pre className="mt-1 p-2 bg-gray-100 rounded text-xs overflow-auto">
                      {JSON.stringify(acceptSelection, null, 2)}
                    </pre>
                    <button
                      type="button"
                      className="mt-2 bg-green-600 hover:bg-green-700 text-white rounded px-3 py-1 disabled:opacity-50"
                      disabled={submitting}
                      onClick={submitDecision}
                    >
                      {submitting ? 'Saving…' : 'Accept and save'}
                    </button>
                  </div>
                )}
                {!acceptSelection && entry && queueStatus === 'needs_review' && (
                  <p className="text-amber-700">No candidate selection available; add logic or skip.</p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
