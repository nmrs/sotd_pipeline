import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import {
  ChevronLeft,
  ChevronRight,
  Check,
  RotateCcw,
  Filter,
  SortAsc,
  BarChart3,
  Loader2,
} from 'lucide-react';
import MonthSelector from '../components/forms/MonthSelector';
import ErrorDisplay from '../components/feedback/ErrorDisplay';
import {
  getBrushValidationData,
  getBrushValidationStatistics,
  recordBrushValidationAction,
  BrushValidationEntry,
  BrushValidationStatistics,
  handleApiError,
} from '../services/api';

type SystemType = 'legacy' | 'scoring';
type SortType = 'unvalidated' | 'validated' | 'ambiguity';

interface OverrideState {
  entryIndex: number;
  selectedStrategy: number;
}

const BrushValidation: React.FC = () => {
  // State management
  const [selectedMonths, setSelectedMonths] = useState<string[]>([]);
  const [selectedSystem, setSelectedSystem] = useState<SystemType>('legacy');
  const [sortBy, setSortBy] = useState<SortType>('unvalidated');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(20);
  const [showValidated, setShowValidated] = useState(true);

  // Data state
  const [entries, setEntries] = useState<BrushValidationEntry[]>([]);
  const [statistics, setStatistics] = useState<BrushValidationStatistics | null>(null);
  const [pagination, setPagination] = useState<{
    page: number;
    page_size: number;
    total: number;
    pages: number;
  } | null>(null);

  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [overrideState, setOverrideState] = useState<OverrideState | null>(null);
  const [actionInProgress, setActionInProgress] = useState<Set<number>>(new Set());

  const currentMonth = selectedMonths[0] || '';

  // Load validation data
  const loadValidationData = useCallback(async () => {
    if (!currentMonth) {
      setEntries([]);
      setPagination(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await getBrushValidationData(currentMonth, selectedSystem, {
        sortBy,
        page: currentPage,
        pageSize,
      });

      setEntries(response.entries);
      setPagination(response.pagination);
    } catch (err) {
      setError(handleApiError(err));
    } finally {
      setLoading(false);
    }
  }, [currentMonth, selectedSystem, sortBy, currentPage, pageSize]);

  // Load statistics
  const loadStatistics = useCallback(async () => {
    if (!currentMonth) {
      setStatistics(null);
      return;
    }

    try {
      const stats = await getBrushValidationStatistics(currentMonth);
      setStatistics(stats);
    } catch (err) {
      console.error('Error loading statistics:', err);
    }
  }, [currentMonth]);

  // Effects
  useEffect(() => {
    loadValidationData();
  }, [loadValidationData]);

  useEffect(() => {
    loadStatistics();
  }, [loadStatistics]);

  useEffect(() => {
    setCurrentPage(1); // Reset to first page when filters change
  }, [selectedSystem, sortBy]);

  // Handle month selection
  const handleMonthsChange = useCallback((months: string[]) => {
    setSelectedMonths(months);
    setCurrentPage(1);
  }, []);

  // Handle system change
  const handleSystemChange = useCallback((system: SystemType) => {
    setSelectedSystem(system);
    setOverrideState(null);
  }, []);

  // Handle sort change
  const handleSortChange = useCallback((sort: SortType) => {
    setSortBy(sort);
  }, []);

  // Handle pagination
  const handlePageChange = useCallback((page: number) => {
    setCurrentPage(page);
  }, []);

  // Handle validation action
  const handleValidate = useCallback(
    async (entryIndex: number) => {
      const entry = entries[entryIndex];
      if (!entry || !currentMonth) return;

      setActionInProgress((prev) => new Set(prev).add(entryIndex));

      try {
        const systemChoice =
          entry.system_used === 'legacy'
            ? {
                strategy: 'legacy',
                score: null,
                result: entry.matched || {},
              }
            : entry.best_result || { strategy: '', score: 0, result: {} };

        await recordBrushValidationAction({
          input_text: entry.input_text,
          month: currentMonth,
          system_used: entry.system_used,
          action: 'validate',
          system_choice: systemChoice,
          user_choice: systemChoice,
          all_brush_strategies: entry.all_strategies,
        });

        // Reload data to reflect changes
        await loadValidationData();
        await loadStatistics();
      } catch (err) {
        setError(handleApiError(err));
      } finally {
        setActionInProgress((prev) => {
          const newSet = new Set(prev);
          newSet.delete(entryIndex);
          return newSet;
        });
      }
    },
    [entries, currentMonth, loadValidationData, loadStatistics]
  );

  // Handle override action
  const handleOverride = useCallback(
    async (entryIndex: number, strategyIndex: number) => {
      const entry = entries[entryIndex];
      if (!entry || !currentMonth || entry.system_used === 'legacy') return;

      setActionInProgress((prev) => new Set(prev).add(entryIndex));

      try {
        const systemChoice = entry.best_result || { strategy: '', score: 0, result: {} };
        const userChoice = entry.all_strategies[strategyIndex];

        await recordBrushValidationAction({
          input_text: entry.input_text,
          month: currentMonth,
          system_used: entry.system_used,
          action: 'override',
          system_choice: systemChoice,
          user_choice: userChoice,
          all_brush_strategies: entry.all_strategies,
        });

        // Reload data to reflect changes
        await loadValidationData();
        await loadStatistics();
        setOverrideState(null);
      } catch (err) {
        setError(handleApiError(err));
      } finally {
        setActionInProgress((prev) => {
          const newSet = new Set(prev);
          newSet.delete(entryIndex);
          return newSet;
        });
      }
    },
    [entries, currentMonth, loadValidationData, loadStatistics]
  );

  // Memoized filtered entries (for display purposes)
  const filteredEntries = useMemo(() => {
    if (showValidated) return entries;
    // Note: In practice, filtering should be done server-side
    // This is just for UI demonstration
    return entries;
  }, [entries, showValidated]);

  if (error) {
    return (
      <div className="w-full p-4">
        <ErrorDisplay error={error} onRetry={() => loadValidationData()} />
      </div>
    );
  }

  return (
    <div className="w-full p-4 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Brush Validation</h1>
        <Badge variant="outline" className="text-sm">
          Multi-System Validation Interface
        </Badge>
      </div>

      {/* Month Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Month Selection</CardTitle>
        </CardHeader>
        <CardContent>
          <MonthSelector selectedMonths={selectedMonths} onMonthsChange={handleMonthsChange} />
        </CardContent>
      </Card>

      {/* Controls */}
      {currentMonth && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* System Selection */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">System</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button
                variant={selectedSystem === 'legacy' ? 'default' : 'outline'}
                onClick={() => handleSystemChange('legacy')}
                className="w-full"
              >
                Legacy System
              </Button>
              <Button
                variant={selectedSystem === 'scoring' ? 'default' : 'outline'}
                onClick={() => handleSystemChange('scoring')}
                className="w-full"
              >
                Scoring System
              </Button>
            </CardContent>
          </Card>

          {/* Sort Options */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <SortAsc className="h-4 w-4" />
                Sort Order
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button
                variant={sortBy === 'unvalidated' ? 'default' : 'outline'}
                onClick={() => handleSortChange('unvalidated')}
                className="w-full"
              >
                Sort by Unvalidated
              </Button>
              <Button
                variant={sortBy === 'validated' ? 'default' : 'outline'}
                onClick={() => handleSortChange('validated')}
                className="w-full"
              >
                Sort by Validated
              </Button>
              {selectedSystem === 'scoring' && (
                <Button
                  variant={sortBy === 'ambiguity' ? 'default' : 'outline'}
                  onClick={() => handleSortChange('ambiguity')}
                  className="w-full"
                >
                  Sort by Ambiguity
                </Button>
              )}
            </CardContent>
          </Card>

          {/* Statistics */}
          {statistics && (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <BarChart3 className="h-4 w-4" />
                  Statistics
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="text-sm">
                  <div className="flex justify-between">
                    <span>Total Entries:</span>
                    <span className="font-medium">{statistics.total_entries}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Validated:</span>
                    <span className="font-medium text-green-600">{statistics.validated_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Overridden:</span>
                    <span className="font-medium text-orange-600">{statistics.overridden_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Unvalidated:</span>
                    <span className="font-medium text-red-600">{statistics.unvalidated_count}</span>
                  </div>
                  <Separator className="my-2" />
                  <div className="flex justify-between font-medium">
                    <span>Validation Rate:</span>
                    <span>{(statistics.validation_rate * 100).toFixed(1)}%</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Filter Options */}
      {currentMonth && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <Filter className="h-4 w-4" />
              Display Options
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Button
              variant={showValidated ? 'outline' : 'default'}
              onClick={() => setShowValidated(!showValidated)}
              className="flex items-center gap-2"
            >
              {showValidated ? 'Hide Validated' : 'Show Validated'}
              <Badge variant="secondary">{statistics?.validated_count || 0}</Badge>
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Loading State */}
      {loading && (
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-center space-x-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Loading validation data...</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Entries List */}
      {!loading && filteredEntries.length > 0 && (
        <div className="space-y-4">
          {filteredEntries.map((entry, index) => (
            <Card key={index} className="relative">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">{entry.input_text}</CardTitle>
                  <div className="flex items-center gap-2">
                    <Badge variant={entry.system_used === 'legacy' ? 'secondary' : 'default'}>
                      {entry.system_used === 'legacy' ? 'Legacy System' : 'Scoring System'}
                    </Badge>
                    {entry.system_used === 'scoring' && entry.best_result && (
                      <Badge variant="outline">Score: {entry.best_result.score}</Badge>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Entry Details */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* System Results */}
                  <div>
                    <h4 className="font-medium mb-2">System Result:</h4>
                    {entry.system_used === 'legacy' ? (
                      <div className="text-sm space-y-1">
                        <div>
                          <span className="font-medium">Match Type:</span> {entry.match_type || 'Unknown'}
                        </div>
                        {entry.matched ? (
                          <>
                            <div>
                              <span className="font-medium">Brand:</span> {entry.matched.brand}
                            </div>
                            <div>
                              <span className="font-medium">Model:</span> {entry.matched.model}
                            </div>
                            {entry.matched.handle && (
                              <div>
                                <span className="font-medium">Handle:</span> {entry.matched.handle.brand}{' '}
                                {entry.matched.handle.model}
                              </div>
                            )}
                            {entry.matched.knot && (
                              <div>
                                <span className="font-medium">Knot:</span> {entry.matched.knot.brand}{' '}
                                {entry.matched.knot.model}
                                {entry.matched.knot.fiber && ` (${entry.matched.knot.fiber})`}
                              </div>
                            )}
                          </>
                        ) : (
                          <div>No match found</div>
                        )}
                      </div>
                    ) : (
                      <div className="text-sm space-y-1">
                        {entry.best_result ? (
                          <>
                            <div>
                              <span className="font-medium">Strategy:</span> {entry.best_result.strategy}
                            </div>
                            <div>
                              <span className="font-medium">Score:</span> {entry.best_result.score}
                            </div>
                            <div>
                              <span className="font-medium">Brand:</span> {entry.best_result.result.brand}
                            </div>
                            <div>
                              <span className="font-medium">Model:</span> {entry.best_result.result.model}
                            </div>
                            {entry.best_result.result.handle && (
                              <div>
                                <span className="font-medium">Handle:</span>{' '}
                                {entry.best_result.result.handle.brand} {entry.best_result.result.handle.model}
                              </div>
                            )}
                            {entry.best_result.result.knot && (
                              <div>
                                <span className="font-medium">Knot:</span> {entry.best_result.result.knot.brand}{' '}
                                {entry.best_result.result.knot.model}
                                {entry.best_result.result.knot.fiber && ` (${entry.best_result.result.knot.fiber})`}
                              </div>
                            )}
                          </>
                        ) : (
                          <div>No match found</div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Alternative Strategies (Scoring System Only) */}
                  {entry.system_used === 'scoring' && entry.all_strategies.length > 0 && (
                    <div>
                      <h4 className="font-medium mb-2">Alternative Strategies:</h4>
                      <div className="text-sm space-y-1 max-h-32 overflow-y-auto">
                        {entry.all_strategies.map((strategy, strategyIndex) => (
                          <div
                            key={strategyIndex}
                            className={`p-2 rounded ${
                              overrideState?.entryIndex === index && overrideState?.selectedStrategy === strategyIndex
                                ? 'bg-blue-50 border border-blue-200'
                                : 'bg-gray-50'
                            }`}
                          >
                            <div className="flex justify-between items-center">
                              <span className="font-medium">{strategy.strategy}</span>
                              <Badge variant="outline">Score: {strategy.score}</Badge>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Override Strategy Selection */}
                {overrideState?.entryIndex === index && entry.system_used === 'scoring' && (
                  <div className="border-t pt-4">
                    <h4 className="font-medium mb-2">Select Alternative Strategy:</h4>
                    <div className="space-y-2">
                      {entry.all_strategies.map((strategy, strategyIndex) => (
                        <Button
                          key={strategyIndex}
                          variant={overrideState.selectedStrategy === strategyIndex ? 'default' : 'outline'}
                          onClick={() =>
                            setOverrideState({
                              entryIndex: index,
                              selectedStrategy: strategyIndex,
                            })
                          }
                          className="w-full justify-between"
                        >
                          <span>
                            {strategy.strategy} ({strategy.score})
                          </span>
                        </Button>
                      ))}
                    </div>
                    <div className="flex gap-2 mt-4">
                      <Button
                        onClick={() => handleOverride(index, overrideState.selectedStrategy)}
                        disabled={actionInProgress.has(index)}
                        className="flex items-center gap-2"
                      >
                        {actionInProgress.has(index) ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Check className="h-4 w-4" />
                        )}
                        Confirm Override
                      </Button>
                      <Button variant="outline" onClick={() => setOverrideState(null)}>
                        Cancel
                      </Button>
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                {overrideState?.entryIndex !== index && (
                  <div className="flex gap-2 pt-4 border-t">
                    <Button
                      onClick={() => handleValidate(index)}
                      disabled={actionInProgress.has(index)}
                      className="flex items-center gap-2 bg-green-600 hover:bg-green-700"
                    >
                      {actionInProgress.has(index) ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Check className="h-4 w-4" />
                      )}
                      Validate
                    </Button>
                    {entry.system_used === 'scoring' && entry.all_strategies.length > 0 && (
                      <Button
                        variant="outline"
                        onClick={() =>
                          setOverrideState({
                            entryIndex: index,
                            selectedStrategy: 0,
                          })
                        }
                        className="flex items-center gap-2"
                      >
                        <RotateCcw className="h-4 w-4" />
                        Override
                      </Button>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Pagination */}
      {pagination && pagination.pages > 1 && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-600">
                Page {pagination.page} of {pagination.pages} • {pagination.total} total entries
              </div>
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(pagination.page - 1)}
                  disabled={pagination.page <= 1}
                >
                  <ChevronLeft className="h-4 w-4" />
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(pagination.page + 1)}
                  disabled={pagination.page >= pagination.pages}
                >
                  Next
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {!loading && filteredEntries.length === 0 && currentMonth && (
        <Card>
          <CardContent className="p-6 text-center">
            <div className="text-gray-500">
              {entries.length === 0
                ? 'No validation data found for the selected month and system.'
                : 'No entries match the current filter criteria.'}
            </div>
          </CardContent>
        </Card>
      )}

      {/* No Month Selected State */}
      {!currentMonth && (
        <Card>
          <CardContent className="p-6 text-center">
            <div className="text-gray-500">Please select a month to begin validation.</div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default BrushValidation;
