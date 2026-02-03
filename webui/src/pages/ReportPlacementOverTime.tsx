import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  getReportRankingsTables,
  getReportRankingsItems,
  getReportRankingsSeries,
  getReportRankingsPivoted,
  ReportRankingsTable,
  ReportRankingsSeriesResponse,
  ReportRankingsPivotedResponse,
} from '@/services/api';
import { handleApiError } from '@/services/api';
import LoadingSpinner from '@/components/layout/LoadingSpinner';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import CellTooltip from '@/components/ui/tooltip';
import { ChevronDown, X, ArrowUp, ArrowDown, Minus } from 'lucide-react';

const CHART_COLORS = ['hsl(var(--chart-1))', 'hsl(var(--chart-2))', 'hsl(var(--chart-3))', 'hsl(var(--chart-4))', 'hsl(var(--chart-5))'];

const ReportPlacementOverTime: React.FC = () => {
  const [tables, setTables] = useState<ReportRankingsTable[]>([]);
  const [selectedTableId, setSelectedTableId] = useState<string>('');
  const [itemsOptions, setItemsOptions] = useState<string[]>([]);
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [itemToAdd, setItemToAdd] = useState<string>('');
  const [loadingTables, setLoadingTables] = useState(true);
  const [loadingItems, setLoadingItems] = useState(false);
  const [loadingSeries, setLoadingSeries] = useState(false);
  const [series, setSeries] = useState<ReportRankingsSeriesResponse | null>(null);
  const [viewMode, setViewMode] = useState<'by-item' | 'by-position'>('by-item');
  const [pivoted, setPivoted] = useState<ReportRankingsPivotedResponse | null>(null);
  const [loadingPivoted, setLoadingPivoted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTables = useCallback(async () => {
    try {
      setLoadingTables(true);
      setError(null);
      const list = await getReportRankingsTables();
      setTables(list);
      if (selectedTableId && !list.find(t => t.id === selectedTableId)) {
        setSelectedTableId('');
        setSelectedItems([]);
        setSeries(null);
      }
    } catch (err: unknown) {
      setError(handleApiError(err));
    } finally {
      setLoadingTables(false);
    }
  }, [selectedTableId]);

  useEffect(() => {
    fetchTables();
  }, [fetchTables]);

  useEffect(() => {
    if (!selectedTableId) {
      setItemsOptions([]);
      setSelectedItems([]);
      setItemToAdd('');
      setSeries(null);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        setLoadingItems(true);
        setError(null);
        const list = await getReportRankingsItems(selectedTableId);
        if (!cancelled) {
          setItemsOptions(list);
          setSelectedItems([]);
          setSeries(null);
        }
      } catch (err: unknown) {
        if (!cancelled) setError(handleApiError(err));
      } finally {
        if (!cancelled) setLoadingItems(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [selectedTableId]);

  useEffect(() => {
    if (viewMode !== 'by-position' || !selectedTableId) {
      setPivoted(null);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        setLoadingPivoted(true);
        setError(null);
        const data = await getReportRankingsPivoted(selectedTableId);
        if (!cancelled) setPivoted(data);
      } catch (err: unknown) {
        if (!cancelled) setError(handleApiError(err));
      } finally {
        if (!cancelled) setLoadingPivoted(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [viewMode, selectedTableId]);

  const handleLoadSeries = async () => {
    if (!selectedTableId || selectedItems.length === 0) {
      setError('Please select an aggregation and at least one item.');
      return;
    }
    try {
      setLoadingSeries(true);
      setError(null);
      const data = await getReportRankingsSeries(selectedTableId, selectedItems);
      setSeries(data);
    } catch (err: unknown) {
      setError(handleApiError(err));
    } finally {
      setLoadingSeries(false);
    }
  };

  const toggleItem = (item: string, checked: boolean) => {
    if (checked) {
      if (item && !selectedItems.includes(item)) {
        setSelectedItems(prev => [...prev, item]);
      }
    } else {
      setSelectedItems(prev => prev.filter(i => i !== item));
    }
  };

  const addItem = (item: string) => {
    if (item && !selectedItems.includes(item)) {
      setSelectedItems(prev => [...prev, item]);
    }
    setItemToAdd('');
  };

  const removeItem = (item: string) => {
    setSelectedItems(prev => prev.filter(i => i !== item));
  };

  const clearAllItems = () => {
    setSelectedItems([]);
  };

  const chartData = React.useMemo(() => {
    if (!series || series.months.length === 0) return [];
    return series.months.map(month => {
      const point: Record<string, string | number> = { month };
      series.series.forEach(entry => {
        const d = entry.data.find(p => p.month === month);
        point[entry.item] = d?.rank ?? '';
        point[`${entry.item}_shaves`] = d?.shaves ?? '';
      });
      return point;
    });
  }, [series]);

  const maxRank = React.useMemo(() => {
    if (!series) return 10;
    let m = 0;
    series.series.forEach(entry => {
      entry.data.forEach(p => {
        if (p.rank != null && p.rank > m) m = p.rank;
      });
    });
    return m || 10;
  }, [series]);

  return (
    <div className="w-full p-4 max-w-full overflow-x-hidden">
      <div className="mb-4">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Rankings over time</h1>
        <p className="text-gray-600">
          Choose an aggregation and one or more items to see how they ranked month over month.
        </p>
      </div>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle>Controls</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-2">
            <Label>Aggregation</Label>
            <Select
              value={selectedTableId}
              onValueChange={setSelectedTableId}
              disabled={loadingTables}
            >
              <SelectTrigger>
                <SelectValue placeholder={loadingTables ? 'Loading…' : 'Select aggregation'} />
              </SelectTrigger>
              <SelectContent>
                {tables.map(t => (
                  <SelectItem key={t.id} value={t.id}>
                    {t.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {selectedTableId && (
            <div className="grid gap-2">
              <Label>View</Label>
              <Tabs value={viewMode} onValueChange={v => setViewMode(v as 'by-item' | 'by-position')}>
                <TabsList>
                  <TabsTrigger value="by-item">By item</TabsTrigger>
                  <TabsTrigger value="by-position">By position</TabsTrigger>
                </TabsList>
              </Tabs>
            </div>
          )}

          {selectedTableId && viewMode === 'by-item' && (
            <div className="grid gap-2">
              <Label>Items to track</Label>
              <div className="flex flex-wrap gap-2 items-center">
                <Select
                  value={itemToAdd}
                  onValueChange={v => {
                    setItemToAdd(v);
                    addItem(v);
                  }}
                  disabled={loadingItems}
                >
                  <SelectTrigger className="w-[280px]">
                    <SelectValue placeholder={loadingItems ? 'Loading…' : 'Add an item'} />
                  </SelectTrigger>
                  <SelectContent>
                    {itemsOptions
                      .filter(i => !selectedItems.includes(i))
                      .map(i => (
                        <SelectItem key={i} value={i}>
                          {i}
                        </SelectItem>
                      ))}
                  </SelectContent>
                </Select>
                {selectedItems.map(item => (
                  <Badge
                    key={item}
                    variant="secondary"
                    className="pl-2 pr-1 py-1 gap-1 cursor-pointer"
                    onClick={() => removeItem(item)}
                  >
                    {item}
                    <X className="h-3 w-3" />
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {viewMode === 'by-item' && (
            <Button
              onClick={handleLoadSeries}
              disabled={!selectedTableId || selectedItems.length === 0 || loadingSeries}
            >
              {loadingSeries ? (
                <>
                  <LoadingSpinner className="mr-2 h-4 w-4" />
                  Loading…
                </>
              ) : (
                'Load series'
              )}
            </Button>
          )}

          {error && (
            <p className="text-sm text-destructive" role="alert">
              {error}
            </p>
          )}
        </CardContent>
      </Card>

      {viewMode === 'by-position' && selectedTableId && (
        <Card className="mb-4">
          <CardHeader>
            <CardTitle>Swim lanes (top 20)</CardTitle>
            <p className="text-sm text-muted-foreground">
              Who was in each rank each month. ↑ moved up, ↓ moved down, — same or first month.
            </p>
          </CardHeader>
          <CardContent>
            {loadingPivoted && (
              <div className="flex items-center justify-center py-8">
                <LoadingSpinner className="h-8 w-8" />
              </div>
            )}
            {!loadingPivoted && pivoted && (pivoted.months.length === 0 || !pivoted.lanes.length) && (
              <p className="text-muted-foreground py-4">No pivoted data for this aggregation.</p>
            )}
            {!loadingPivoted && pivoted && pivoted.months.length > 0 && pivoted.lanes.length > 0 && (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="sticky left-0 z-10 bg-background min-w-[4rem]">Rank</TableHead>
                      {pivoted.months.map(m => (
                        <TableHead key={m} className="whitespace-nowrap">
                          {m}
                        </TableHead>
                      ))}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {pivoted.lanes.map(lane => (
                      <TableRow key={lane.rank}>
                        <TableCell className="font-medium sticky left-0 z-10 bg-background">
                          {lane.rank}
                        </TableCell>
                        {lane.points.map(pt => {
                          const currentRank = lane.rank;
                          const prevRank = pt.prev_rank;
                          let arrow: React.ReactNode = null;
                          if (prevRank !== null && prevRank !== undefined) {
                            if (prevRank > currentRank) arrow = <ArrowUp className="h-3 w-3 inline text-green-600" />;
                            else if (prevRank < currentRank) arrow = <ArrowDown className="h-3 w-3 inline text-red-600" />;
                            else arrow = <Minus className="h-3 w-3 inline text-muted-foreground" />;
                          }
                          const tooltipParts = [pt.item ?? ''];
                          if (pt.shaves != null) tooltipParts.push(`${pt.shaves} shaves`);
                          if (prevRank != null && prevRank !== currentRank) {
                            tooltipParts.push(prevRank > currentRank ? `Moved up from rank ${prevRank}` : `Moved down from rank ${prevRank}`);
                          }
                          const tooltipContent = tooltipParts.filter(Boolean).join(' — ');
                          const cellContent = (
                            <span className="inline-flex items-center gap-1 max-w-[140px] truncate">
                              {pt.item ?? '—'}
                              {arrow}
                            </span>
                          );
                          return (
                            <TableCell key={pt.month} className="whitespace-nowrap">
                              {tooltipContent ? (
                                <CellTooltip content={tooltipContent}>{cellContent}</CellTooltip>
                              ) : (
                                cellContent
                              )}
                            </TableCell>
                          );
                        })}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {series && viewMode === 'by-item' && (
        <>
          <Card className="mb-4">
            <CardHeader>
              <CardTitle>Rank over time</CardTitle>
            </CardHeader>
            <CardContent>
              {chartData.length === 0 ? (
                <p className="text-muted-foreground">No data for the selected aggregation and items.</p>
              ) : (
                <div className="h-[400px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData} margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
                      <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                      <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                      <YAxis
                        domain={[maxRank + 1, 1]}
                        tick={{ fontSize: 12 }}
                        label={{ value: 'Rank (1 = top)', angle: -90, position: 'insideLeft' }}
                      />
                      <Tooltip
                        formatter={(value, name) => {
                          if (typeof name === 'string' && name.endsWith('_shaves')) return [value, 'Shaves'];
                          return [value, name];
                        }}
                        labelFormatter={label => `Month: ${label}`}
                      />
                      <Legend />
                      {series.series.map((entry, i) => (
                        <Line
                          key={entry.item}
                          type="monotone"
                          dataKey={entry.item}
                          stroke={CHART_COLORS[i % CHART_COLORS.length]}
                          strokeWidth={2}
                          dot={{ r: 3 }}
                          connectNulls={false}
                          name={entry.item}
                        />
                      ))}
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Data table</CardTitle>
            </CardHeader>
            <CardContent>
              {chartData.length === 0 ? (
                <p className="text-muted-foreground">No data to show.</p>
              ) : (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Month</TableHead>
                        {series.series.map(entry => (
                          <TableHead key={entry.item}>{entry.item}</TableHead>
                        ))}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {chartData.map(row => (
                        <TableRow key={row.month}>
                          <TableCell className="font-medium">{row.month}</TableCell>
                          {series.series.map(entry => {
                            const rank = row[entry.item];
                            const shaves = row[`${entry.item}_shaves`];
                            const cell =
                              rank !== '' && rank !== undefined
                                ? shaves !== '' && shaves !== undefined
                                  ? `#${rank} (${shaves})`
                                  : `#${rank}`
                                : '—';
                            return (
                              <TableCell key={entry.item}>{cell}</TableCell>
                            );
                          })}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}

      {viewMode === 'by-item' && !series && selectedTableId && selectedItems.length > 0 && !loadingSeries && !error && (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            Click &quot;Load series&quot; to load rank-over-time data.
          </CardContent>
        </Card>
      )}

      {!selectedTableId && !loadingTables && (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            Choose an aggregation and one or more items to see how they placed over time.
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ReportPlacementOverTime;
