import React, { useState, useEffect, useMemo, useCallback } from 'react';
import MonthSelector from '../components/forms/MonthSelector';
import { BrushSplitTable } from '../components/data/BrushSplitTable';
import { BrushSplit } from '../types/brushSplit';
import { Button } from '@/components/ui/button';
import { Eye, EyeOff } from 'lucide-react';
import CommentModal from '../components/domain/CommentModal';
import { getCommentDetail, CommentDetail, saveBrushSplits } from '../services/api';

const BrushSplitValidator: React.FC = () => {
  const [brushSplits, setBrushSplits] = useState<BrushSplit[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedMonths, setSelectedMonths] = useState<string[]>([]);
  const [showValidated, setShowValidated] = useState(false);
  const [showMatched, setShowMatched] = useState(false);
  const [selectedComment, setSelectedComment] = useState<CommentDetail | null>(null);
  const [commentModalOpen, setCommentModalOpen] = useState(false);
  const [commentLoading, setCommentLoading] = useState(false);

  // Load brush splits when months are selected
  useEffect(() => {
    if (selectedMonths.length === 0) {
      setBrushSplits([]);
      return;
    }

    const loadBrushSplits = async () => {
      try {
        setLoading(true);
        console.log('Loading brush splits for months:', selectedMonths);

        const response = await fetch('/api/brush-splits', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ months: selectedMonths }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('Received brush splits data:', data);

        // Extract the brush_splits array from the response
        const brushSplitsArray = data.brush_splits || [];
        console.log('Number of brush splits:', brushSplitsArray.length);

        if (brushSplitsArray.length > 0) {
          console.log('First brush split:', brushSplitsArray[0]);
        }

        setBrushSplits(brushSplitsArray);
      } catch (error) {
        console.error('Error loading brush splits:', error);
        setError('Failed to load brush splits');
      } finally {
        setLoading(false);
      }
    };

    loadBrushSplits();
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

  const handleCommentClick = useCallback(
    async (commentId: string) => {
      try {
        setCommentLoading(true);
        const comment = await getCommentDetail(commentId, selectedMonths);
        setSelectedComment(comment);
        setCommentModalOpen(true);
      } catch (err: unknown) {
        console.error('Error loading comment detail:', err);
        // Don't show error to user, just log it
      } finally {
        setCommentLoading(false);
      }
    },
    [selectedMonths]
  );

  // Create the show/hide validated button
  const validatedButton = useMemo(() => {
    if (brushSplits.length === 0) return null;

    return (
      <Button
        variant='outline'
        size='sm'
        onClick={handleToggleValidated}
        className='flex items-center gap-2'
      >
        {showValidated ? (
          <>
            <EyeOff className='h-4 w-4' />
            Hide Validated
          </>
        ) : (
          <>
            <Eye className='h-4 w-4' />
            Show Validated ({hiddenValidatedCount})
          </>
        )}
      </Button>
    );
  }, [brushSplits.length, showValidated, hiddenValidatedCount, handleToggleValidated]);

  // Create the show/hide matched button
  const matchedButton = useMemo(() => {
    if (brushSplits.length === 0) return null;

    return (
      <Button
        variant='outline'
        size='sm'
        onClick={() => setShowMatched(!showMatched)}
        className='flex items-center gap-2'
      >
        {showMatched ? (
          <>
            <EyeOff className='h-4 w-4' />
            Hide Matched
          </>
        ) : (
          <>
            <Eye className='h-4 w-4' />
            Show Matched
          </>
        )}
      </Button>
    );
  }, [brushSplits.length, showMatched]);

  return (
    <div className='container mx-auto p-4'>
      <div className='mb-4'>
        <MonthSelector selectedMonths={selectedMonths} onMonthsChange={setSelectedMonths} />
      </div>

      {error && (
        <div className='mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded'>
          Error: {error}
        </div>
      )}

      {loading && (
        <div className='mb-4 p-4 bg-blue-100 border border-blue-400 text-blue-700 rounded'>
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
            } catch (error: unknown) {
              console.error('Error saving brush splits:', error);
              const errorMessage = error instanceof Error ? error.message : 'Unknown error';
              setError(`Error saving brush splits: ${errorMessage}`);
            }
          }}
          customControls={
            <div className='flex gap-2'>
              {validatedButton}
              {matchedButton}
            </div>
          }
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
