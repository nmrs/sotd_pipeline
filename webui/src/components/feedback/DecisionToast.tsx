import React, { useEffect, useState } from 'react';

export type DecisionAction =
  | 'mark_correct'
  | 'remove_correct'
  | 'mark_unmatched'
  | 'mark_incorrect';

export interface PendingDecision {
  id: string;
  action: DecisionAction;
  field: string;
  /** Number of items affected (for display) */
  itemCount: number;
  /** Keys added to pendingItems — needed for undo */
  itemKeys: Set<string>;
  /** The async function that fires the actual API call */
  execute: () => Promise<void>;
  /** setTimeout id — cleared on undo */
  timerId: ReturnType<typeof setTimeout>;
  createdAt: number;
}

const ACTION_LABELS: Record<DecisionAction, string> = {
  mark_correct: 'Marked as correct',
  remove_correct: 'Removed from correct',
  mark_unmatched: 'Marked as unmatched',
  mark_incorrect: 'Marked as incorrect',
};

const UNDO_DELAY_MS = 5000;

interface DecisionToastProps {
  decisions: PendingDecision[];
  onUndo: (id: string) => void;
}

const DecisionToastItem: React.FC<{
  decision: PendingDecision;
  onUndo: (id: string) => void;
}> = ({ decision, onUndo }) => {
  const [progress, setProgress] = useState(100);

  useEffect(() => {
    const startTime = decision.createdAt;
    const endTime = startTime + UNDO_DELAY_MS;

    const tick = () => {
      const now = Date.now();
      const remaining = Math.max(0, endTime - now);
      setProgress((remaining / UNDO_DELAY_MS) * 100);
      if (remaining > 0) {
        frameId = requestAnimationFrame(tick);
      }
    };

    let frameId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frameId);
  }, [decision.createdAt]);

  return (
    <div className='bg-gray-800 text-white rounded-lg shadow-lg px-4 py-3 flex items-center gap-3 min-w-[300px] max-w-[420px]'>
      <div className='flex-1 min-w-0'>
        <div className='text-sm font-medium truncate'>
          {ACTION_LABELS[decision.action]} ({decision.itemCount}{' '}
          {decision.itemCount === 1 ? 'item' : 'items'})
        </div>
        <div className='mt-1.5 h-1 bg-gray-600 rounded-full overflow-hidden'>
          <div
            className='h-full bg-blue-400 rounded-full transition-none'
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
      <button
        onClick={() => onUndo(decision.id)}
        className='px-3 py-1 text-sm font-medium bg-white text-gray-800 rounded hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-white whitespace-nowrap'
      >
        Undo
      </button>
    </div>
  );
};

const DecisionToast: React.FC<DecisionToastProps> = ({ decisions, onUndo }) => {
  if (decisions.length === 0) return null;

  return (
    <div className='fixed bottom-4 right-4 z-50 flex flex-col gap-2'>
      {decisions.map(d => (
        <DecisionToastItem key={d.id} decision={d} onUndo={onUndo} />
      ))}
    </div>
  );
};

export { UNDO_DELAY_MS };
export default DecisionToast;
