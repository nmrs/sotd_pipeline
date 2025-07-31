import React, { useState, useEffect, useMemo, useCallback } from 'react';
import MonthSelector from '../components/forms/MonthSelector';
import { BrushSplitTable } from '../components/data/BrushSplitTable';
import { BrushSplit } from '../types/brushSplit';
import { Button } from '@/components/ui/button';
import { Eye, EyeOff, FileText, Save } from 'lucide-react';
import CommentModal from '../components/domain/CommentModal';
import { getCommentDetail, CommentDetail, saveBrushSplits, loadBrushSplits, loadYamlBrushSplits } from '../services/api';
import { handleApiError } from '../services/api';

const BrushSplitValidator: React.FC = () => {
  const [brushSplits, setBrushSplits] = useState<BrushSplit[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedMonths, setSelectedMonths] = useState<string[]>([]);
  const [showValidated, setShowValidated] = useState(true);
  const [showMatched, setShowMatched] = useState(true);
  const [showYaml, setShowYaml] = useState(false);
  const [yamlBrushSplits, setYamlBrushSplits] = useState<BrushSplit[]>([]);
  const [yamlLoading, setYamlLoading] = useState(false);
  const [yamlError, setYamlError] = useState<string | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [saving, setSaving] = useState(false);
  const [selectedComment, setSelectedComment] = useState<CommentDetail | null>(null);
  const [commentModalOpen, setCommentModalOpen] = useState(false);
  const [commentLoading, setCommentLoading] = useState(false);
  // Multi-comment navigation state
  const [allComments, setAllComments] = useState<CommentDetail[]>([]);
  const [currentCommentIndex, setCurrentCommentIndex] = useState<number>(0);
  const [remainingCommentIds, setRemainingCommentIds] = useState<string[]>([]);

  // Load brush splits from selected months
  const loadData = async () => {
    if (selectedMonths.length === 0) {
      setBrushSplits([]);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await loadBrushSplits(selectedMonths, !showMatched);
      setBrushSplits(response.brush_splits);
    } catch (err) {
      setError(handleApiError(err));
    } finally {
      setLoading(false);
    }
  };

  // Load YAML brush splits
  const loadYamlData = async () => {
    setYamlLoading(true);
    setYamlError(null);

    try {
      const response = await loadYamlBrushSplits();
      setYamlBrushSplits(response.brush_splits);
    } catch (err) {
      setYamlError(handleApiError(err));
    } finally {
      setYamlLoading(false);
    }
  };

  // Load brush splits when months are selected
  useEffect(() => {
    loadData();
  }, [selectedMonths, showMatched]);

  // Count matched items that would be hidden/shown
  const matchedCount = useMemo(() => {
    return brushSplits.filter(split => split.match_type && split.match_type !== 'None').length;
  }, [brushSplits]);

  // Count YAML entries
  const yamlCount = useMemo(() => {
    return yamlBrushSplits.length;
  }, [yamlBrushSplits]);

  // Combine pipeline data and YAML data based on filters
  const filteredBrushSplits = useMemo(() => {
    let combinedData = [...brushSplits];

    // Add YAML data if enabled
    if (showYaml) {
      combinedData = [...combinedData, ...yamlBrushSplits];
    }

    // Filter by validation status
    if (!showValidated) {
      combinedData = combinedData.filter(split => !split.validated);
    }

    return combinedData;
  }, [brushSplits, yamlBrushSplits, showYaml, showValidated]);

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
    async (commentId: string, allCommentIds?: string[]) => {
      try {
        setCommentLoading(true);

        // Always load just the clicked comment initially for fast response
        const comment = await getCommentDetail(commentId, selectedMonths);
        setSelectedComment(comment);
        setCurrentCommentIndex(0);
        setCommentModalOpen(true);

        // Store the comment IDs for potential future loading
        if (allCommentIds && allCommentIds.length > 1) {
          setAllComments([comment]); // Start with just the first comment
          // Store the remaining IDs for lazy loading
          setRemainingCommentIds(allCommentIds.filter(id => id !== commentId));
        } else {
          setAllComments([comment]);
          setRemainingCommentIds([]);
        }
      } catch (err: unknown) {
        console.error('Error loading comment detail:', err);
        // Don't show error to user, just log it
      } finally {
        setCommentLoading(false);
      }
    },
    [selectedMonths]
  );

  const handleCommentNavigation = async (direction: 'prev' | 'next') => {
    if (allComments.length <= 1 && remainingCommentIds.length === 0) return;

    let newIndex = currentCommentIndex;
    if (direction === 'prev') {
      newIndex = Math.max(0, currentCommentIndex - 1);
      setCurrentCommentIndex(newIndex);
      setSelectedComment(allComments[newIndex]);
    } else {
      // Next - check if we need to load more comments
      if (currentCommentIndex === allComments.length - 1 && remainingCommentIds.length > 0) {
        // Load the next comment
        try {
          setCommentLoading(true);
          const nextCommentId = remainingCommentIds[0];
          const nextComment = await getCommentDetail(nextCommentId, selectedMonths);

          setAllComments(prev => [...prev, nextComment]);
          setRemainingCommentIds(prev => prev.slice(1));
          setCurrentCommentIndex(allComments.length);
          setSelectedComment(nextComment);
        } catch (err: unknown) {
          console.error('Error loading comment detail:', err);
        } finally {
          setCommentLoading(false);
        }
      } else {
        // Navigate to existing comment
        newIndex = Math.min(allComments.length - 1, currentCommentIndex + 1);
        setCurrentCommentIndex(newIndex);
        setSelectedComment(allComments[newIndex]);
      }
    }
  };

  const handleCloseCommentModal = () => {
    setCommentModalOpen(false);
    setSelectedComment(null);
    setAllComments([]);
    setCurrentCommentIndex(0);
    setRemainingCommentIds([]);
  };

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
            Hide Matched ({matchedCount})
          </>
        ) : (
          <>
            <Eye className='h-4 w-4' />
            Show Matched ({matchedCount})
          </>
        )}
      </Button>
    );
  }, [brushSplits.length, showMatched, matchedCount]);

  // Create the show/hide YAML button
  const yamlButton = useMemo(() => {
    return (
      <Button
        variant='outline'
        size='sm'
        onClick={() => {
          if (!showYaml && yamlBrushSplits.length === 0) {
            // Load YAML data when first enabling
            loadYamlData();
          }
          setShowYaml(!showYaml);
        }}
        className='flex items-center gap-2'
        disabled={yamlLoading}
      >
        {showYaml ? (
          <>
            <EyeOff className='h-4 w-4' />
            Hide YAML ({yamlCount})
          </>
        ) : (
          <>
            <FileText className='h-4 w-4' />
            Show YAML ({yamlCount})
          </>
        )}
      </Button>
    );
  }, [showYaml, yamlCount, yamlLoading, yamlBrushSplits.length]);

  // Create the save button
  const saveButton = useMemo(() => {
    if (!hasUnsavedChanges) return null;

    return (
      <Button
        variant='default'
        size='sm'
        onClick={async () => {
          setSaving(true);
          try {
            // This will be handled by the onSave callback in BrushSplitTable
            // We just need to trigger the save action
            setHasUnsavedChanges(false);
          } catch (error) {
            console.error('Error saving:', error);
          } finally {
            setSaving(false);
          }
        }}
        disabled={saving}
        className='flex items-center gap-2 bg-green-600 hover:bg-green-700'
      >
        <Save className='h-4 w-4' />
        {saving ? 'Saving...' : 'Save Changes'}
      </Button>
    );
  }, [hasUnsavedChanges, saving]);

  return (
    <div className='w-full p-4'>
      <div className='mb-4'>
        <MonthSelector selectedMonths={selectedMonths} onMonthsChange={setSelectedMonths} />
      </div>

      {/* Help section */}
      <div className='mb-4 p-4 bg-gray-50 border border-gray-200 rounded'>
        <h3 className='font-semibold mb-2'>How to validate brush splits:</h3>
        <ul className='text-sm text-gray-600 space-y-1'>
          <li>• <strong>Edit fields:</strong> Click on handle or knot fields to edit them</li>
          <li>• <strong>Mark as "Don't Split":</strong> Check the box for brushes that shouldn't be split</li>
          <li>• <strong>Save changes:</strong> Click "Save Changes" when you're done editing</li>
          <li>• <strong>View comments:</strong> Click on comment links to see the original context</li>
        </ul>
      </div>

      {error && (
        <div className='mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded'>
          Error: {error}
        </div>
      )}

      {yamlError && (
        <div className='mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded'>
          YAML Error: {yamlError}
        </div>
      )}

      {loading && (
        <div className='mb-4 p-4 bg-blue-100 border border-blue-400 text-blue-700 rounded'>
          Loading brush splits...
        </div>
      )}

      {yamlLoading && (
        <div className='mb-4 p-4 bg-blue-100 border border-blue-400 text-blue-700 rounded'>
          Loading YAML data...
        </div>
      )}

      {hasUnsavedChanges && (
        <div className='mb-4 p-4 bg-yellow-100 border border-yellow-400 text-yellow-700 rounded flex items-center justify-between'>
          <span>⚠️ You have unsaved changes. Click "Save Changes" to confirm your validation.</span>
          <Button
            variant='default'
            size='sm'
            onClick={async () => {
              setSaving(true);
              try {
                // Trigger save by calling the save function directly
                // This will be handled by the onSave callback
                setHasUnsavedChanges(false);
              } catch (error) {
                console.error('Error saving:', error);
              } finally {
                setSaving(false);
              }
            }}
            disabled={saving}
            className='bg-green-600 hover:bg-green-700'
          >
            <Save className='h-4 w-4 mr-2' />
            {saving ? 'Saving...' : 'Save Changes'}
          </Button>
        </div>
      )}

      {!loading && !error && (
        <div className='w-full'>
          <BrushSplitTable
            brushSplits={filteredBrushSplits}
            onSelectionChange={() => {
              // Note: This callback is available for future use but not currently implemented
            }}
            onSave={async (updatedData: BrushSplit[]) => {
              setSaving(true);
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
                  setHasUnsavedChanges(false); // No unsaved changes after successful save
                } else {
                  console.error('Failed to save brush splits:', response.message);
                  setError(`Failed to save brush splits: ${response.message}`);
                }
              } catch (error: unknown) {
                console.error('Error saving brush splits:', error);
                const errorMessage = error instanceof Error ? error.message : 'Unknown error';
                setError(`Error saving brush splits: ${errorMessage}`);
              } finally {
                setSaving(false);
              }
            }}
            onUnsavedChangesChange={setHasUnsavedChanges}
            customControls={
              <div className='flex gap-2'>
                {validatedButton}
                {matchedButton}
                {yamlButton}
                {saveButton}
              </div>
            }
            onCommentClick={handleCommentClick}
            commentLoading={commentLoading}
          />
        </div>
      )}

      {/* Comment Modal */}
      <CommentModal
        comment={selectedComment}
        isOpen={commentModalOpen}
        onClose={handleCloseCommentModal}
        comments={allComments}
        currentIndex={currentCommentIndex}
        onNavigate={handleCommentNavigation}
        remainingCommentIds={remainingCommentIds}
      />
    </div>
  );
};

export default BrushSplitValidator;
