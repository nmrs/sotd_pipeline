import { OperationStatus } from '@/services/api';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { CheckCircle2, Loader2, XCircle, Clock } from 'lucide-react';

interface OperationProgressProps {
  status: OperationStatus | null;
  error: Error | null;
  isPolling: boolean;
}

export const OperationProgress = ({ status, error, isPolling }: OperationProgressProps) => {
  if (!status && !error && !isPolling) {
    return null;
  }

  if (error) {
    return (
      <Alert variant="destructive" className="mb-4">
        <XCircle className="h-4 w-4" />
        <AlertDescription>
          Error checking operation status: {error.message}
        </AlertDescription>
      </Alert>
    );
  }

  if (!status) {
    return (
      <Alert className="mb-4">
        <Loader2 className="h-4 w-4 animate-spin" />
        <AlertDescription>Initializing operation...</AlertDescription>
      </Alert>
    );
  }

  const progressPercent = Math.round(status.progress * 100);

  let icon;
  let variant: 'default' | 'destructive' = 'default';

  switch (status.status) {
    case 'pending':
      icon = <Clock className="h-4 w-4" />;
      break;
    case 'processing':
      icon = <Loader2 className="h-4 w-4 animate-spin" />;
      break;
    case 'completed':
      icon = <CheckCircle2 className="h-4 w-4" />;
      break;
    case 'failed':
      icon = <XCircle className="h-4 w-4" />;
      variant = 'destructive';
      break;
  }

  return (
    <Alert variant={variant} className="mb-4">
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <AlertDescription className="flex-1">
          <div className="font-medium">{status.message}</div>
          {status.status === 'processing' && (
            <div className="mt-2">
              <div className="w-full bg-secondary rounded-full h-2">
                <div
                  className="bg-primary h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
              <div className="text-xs text-muted-foreground mt-1">{progressPercent}%</div>
            </div>
          )}
          {status.status === 'completed' && status.result && (
            <div className="text-sm mt-1">
              {status.result.marked_count !== undefined && (
                <span>Marked {status.result.marked_count} matches as correct</span>
              )}
              {status.result.removed_count !== undefined && (
                <span>Removed {status.result.removed_count} matches</span>
              )}
              {status.result.errors && status.result.errors.length > 0 && (
                <div className="text-destructive mt-1">
                  {status.result.errors.length} error(s) occurred
                </div>
              )}
            </div>
          )}
          {status.status === 'failed' && status.result?.error && (
            <div className="text-sm mt-1">{status.result.error}</div>
          )}
        </AlertDescription>
      </div>
    </Alert>
  );
};
