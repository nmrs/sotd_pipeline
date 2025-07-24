import React, { useState, useEffect, useMemo, useCallback } from 'react';
import MonthSelector from '../components/forms/MonthSelector';
import { BrushSplitTable } from '../components/data/BrushSplitTable';
import { BrushSplit } from '../types/brushSplit';
import { Button } from '@/components/ui/button';
import { Eye, EyeOff } from 'lucide-react';
import CommentModal from '../components/domain/CommentModal';
import { getCommentDetail, CommentDetail, saveBrushSplits } from '../services/api';

interface LoadResponse {
  brush_splits: BrushSplit[];
  statistics: Record<string, unknown>;
}

const BrushSplitValidator: React.FC = () => {
  const [brushSplits, setBrushSplits] = useState<BrushSplit[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedMonths, setSelectedMonths] = useState<string[]>([]);
  const [showValidated, setShowValidated] = useState(false);
  const [selectedComment, setSelectedComment] = useState<CommentDetail | null>(null);
  const [commentModalOpen, setCommentModalOpen] = useState(false);
  const [commentLoading, setCommentLoading] = useState(false);

  useEffect(() => {
    if (selectedMonths.length === 0) {
      setBrushSplits([]);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);

    // Build query parameters for the API call
    const queryParams = selectedMonths
      .map(month => `months=${encodeURIComponent(month)}`)
      .join('&');

    fetch(`/api/brush-splits/load?${queryParams}`)
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
      })
      .then((data: LoadResponse) => {
        setBrushSplits(data.brush_splits);
        // Reset to show validated items hidden when months change
        setShowValidated(false);
      })
      .catch(error => {
        console.error('Error loading brush splits:', error);
        setError(error.message);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [selectedMonths]);

  // Filter brush splits based on showValidated state
  const filteredBrushSplits = useMemo(() => {
    console.log('Filtering brush splits:', { brushSplits, showValidated });
    if (showValidated) {
      // Show all items (validated + unvalidated)
      return brushSplits;
    } else {
      // Show only unvalidated items
      return brushSplits.filter(split => !split.validated);
    }
  }, [brushSplits, showValidated]);

  // Count validated items that would be hidden
  const hiddenValidatedCount = useMemo(() => {
    if (showValidated) {
      return 0; // All items are shown
    } else {
      return brushSplits.filter(split => split.validated).length;
    }
  }, [brushSplits, showValidated]);

  const handleToggleValidated = useCallback(() => {
    setShowValidated(!showValidated);
  }, [showValidated]);

  const handleCommentClick = useCallback(async (commentId: string) => {
    try {
      setCommentLoading(true);
      const comment = await getCommentDetail(commentId, selectedMonths);
      setSelectedComment(comment);
      setCommentModalOpen(true);
    } catch (err: any) {
      console.error('Error loading comment detail:', err);
      // Don't show error to user, just log it
    } finally {
      setCommentLoading(false);
    }
  }, [selectedMonths]);

  // Create the show/hide validated button
  const validatedButton = useMemo(() => {
    if (brushSplits.length === 0) return null;

    return (
      <Button
        variant="outline"
        size="sm"
        onClick={handleToggleValidated}
        className="flex items-center gap-2"
      >
        {showValidated ? (
          <>
            <EyeOff className="h-4 w-4" />
            Hide Validated
          </>
        ) : (
          <>
            <Eye className="h-4 w-4" />
            Show Validated ({hiddenValidatedCount})
          </>
        )}
      </Button>
    );
  }, [brushSplits.length, showValidated, hiddenValidatedCount, handleToggleValidated]);

  return (
    <div className="container mx-auto p-4">
      <div className="mb-4">
        <MonthSelector
          selectedMonths={selectedMonths}
          onMonthsChange={setSelectedMonths}
        />
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
          Error: {error}
        </div>
      )}

      {loading && (
        <div className="mb-4 p-4 bg-blue-100 border border-blue-400 text-blue-700 rounded">
          Loading brush splits...
        </div>
      )}

      {!loading && !error && (
        <BrushSplitTable
          brushSplits={filteredBrushSplits}
          onSelectionChange={() => {
            // Note: This callback is available for future use but not currently implemented
          }}
          onSave={async (updatedData: BrushSplit[]) => {
            try {
              // Save the validated brush splits to the backend
              const response = await saveBrushSplits(updatedData);

              if (response.success) {
                // Update the local state by merging the validated items with existing unvalidated items
                setBrushSplits(prevSplits => {
                  // Create a map of validated items by original name for quick lookup
                  const validatedMap = new Map(updatedData.map(split => [split.original, split]));

                  // Merge: keep unvalidated items, update validated items
                  return prevSplits.map(split => {
                    const validatedSplit = validatedMap.get(split.original);
                    if (validatedSplit) {
                      // This item was validated and saved
                      return validatedSplit;
                    } else {
                      // This item was not validated, keep as is
                      return split;
                    }
                  });
                });

                console.log(`Successfully saved ${response.saved_count} brush splits`);
              } else {
                console.error('Failed to save brush splits:', response.message);
                setError(`Failed to save brush splits: ${response.message}`);
              }
            } catch (error: any) {
              console.error('Error saving brush splits:', error);
              setError(`Error saving brush splits: ${error.message || 'Unknown error'}`);
            }
          }}
          customControls={validatedButton}
          onCommentClick={handleCommentClick}
          commentLoading={commentLoading}
        />
      )}

      {/* Comment Modal */}
      <CommentModal
        comment={selectedComment}
        isOpen={commentModalOpen}
        onClose={() => {
          setCommentModalOpen(false);
          setSelectedComment(null);
        }}
      />
    </div>
  );
};

export default BrushSplitValidator;
