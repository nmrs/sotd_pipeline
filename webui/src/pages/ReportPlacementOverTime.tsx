import React, { useState, useEffect, useCallback, useRef } from 'react';
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

export type RankChartTooltipProps = {
  active?: boolean;
  payload?: Array<{ payload: Record<string, string | number> }>;
  label?: string;
};
export type RankChartTooltipSeries = { item: string }[];

/** Custom tooltip content for rank-over-time chart: shows rank, shaves, unique users per item. Exported for tests. */
export function RankChartTooltipContent(
  props: RankChartTooltipProps,
  series: RankChartTooltipSeries | null
): React.ReactNode {
  const { active, payload, label } = props;
  if (!active || !payload?.length || !series) return null;
  const row = payload[0].payload;
  const month = row.month ?? label;
  return (
    <div className="rounded-md border bg-background px-3 py-2 text-sm shadow-md">
      <p className="font-medium mb-1.5">Month: {String(month)}</p>
      {series.map((entry, i) => {
        const rank = row[entry.item];
        const shaves = row[`${entry.item}_shaves`];
        const uniqueUsers = row[`${entry.item}_unique_users`];
        const color = CHART_COLORS[i % CHART_COLORS.length];
        const parts: string[] = [];
        if (rank !== '' && rank !== undefined) parts.push(`rank #${rank}`);
        if (shaves !== '' && shaves !== undefined) parts.push(`${shaves} shaves`);
        if (uniqueUsers !== '' && uniqueUsers !== undefined) parts.push(`${uniqueUsers} users`);
        const line = parts.length ? parts.join(', ') : '—';
        return (
          <p key={entry.item} className="flex items-center gap-1.5">
            <span
              className="shrink-0 rounded-full"
              style={{ backgroundColor: color, width: 8, height: 8 }}
              aria-hidden
            />
            <span><strong>{entry.item}:</strong> {line}</span>
          </p>
        );
      })}
    </div>
  );
}

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
  const prevViewModeRef = useRef<'by-item' | 'by-position'>(viewMode);
  const [chartPrimaryMetric, setChartPrimaryMetric] = useState<
    'rank' | 'shaves' | 'unique_users'
  >('rank');

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

  useEffect(() => {
    const prev = prevViewModeRef.current;
    prevViewModeRef.current = viewMode;
    if (prev === 'by-position' && viewMode === 'by-item' && selectedTableId && selectedItems.length > 0) {
      handleLoadSeries();
    }
  }, [viewMode, selectedTableId, selectedItems.length]);

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
    const points = series.months.map(month => {
      const point: Record<string, string | number> = { month };
      series.series.forEach(entry => {
        const d = entry.data.find(p => p.month === month);
        point[entry.item] = d?.rank ?? '';
        point[`${entry.item}_shaves`] = d?.shaves ?? '';
        point[`${entry.item}_unique_users`] = d?.unique_users ?? '';
      });
      return point;
    });
    return points.reverse();
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

  const maxChartValue = React.useMemo(() => {
    if (!series || (chartPrimaryMetric !== 'shaves' && chartPrimaryMetric !== 'unique_users'))
      return 10;
    const field = chartPrimaryMetric === 'shaves' ? 'shaves' : 'unique_users';
    let m = 0;
    series.series.forEach(entry => {
      entry.data.forEach(p => {
        const v = p[field];
        if (v != null && typeof v === 'number' && v > m) m = v;
      });
    });
    const padded = Math.ceil(m * 1.05) || 10;
    return Math.max(padded, 1);
  }, [series, chartPrimaryMetric]);

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
              <div className="flex flex-wrap items-center gap-2">
                <Label className="shrink-0">View</Label>
                <Tabs value={viewMode} onValueChange={v => setViewMode(v as 'by-item' | 'by-position')}>
                  <TabsList>
                    <TabsTrigger value="by-item">By item</TabsTrigger>
                    <TabsTrigger value="by-position">By position</TabsTrigger>
                  </TabsList>
                </Tabs>
                {selectedItems.length > 0 && (
                  <div className="flex flex-wrap gap-2 items-center">
                    {selectedItems.map((item, i) => {
                      const color = CHART_COLORS[i % CHART_COLORS.length];
                      return (
                        <Badge
                          key={item}
                          variant="secondary"
                          className="pl-2 pr-1 py-1 gap-1.5 cursor-pointer border-l-2"
                          style={{ borderLeftColor: color }}
                          onClick={() => removeItem(item)}
                        >
                          <span
                            className="rounded-full shrink-0"
                            style={{ backgroundColor: color, width: 8, height: 8 }}
                            aria-hidden
                          />
                          {item}
                          <X className="h-3 w-3" />
                        </Badge>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          )}

          {selectedTableId && (
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
            {!loadingPivoted && pivoted && pivoted.months.length > 0 && pivoted.lanes.length > 0 && (() => {
              const monthsNewestFirst = [...pivoted.months].reverse();
              return (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="sticky left-0 z-10 bg-background min-w-[4rem]">Rank</TableHead>
                      {monthsNewestFirst.map(m => (
                        <TableHead key={m} className="whitespace-nowrap">
                          {m}
                        </TableHead>
                      ))}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {pivoted.lanes.map(lane => {
                      const pointsNewestFirst = [...lane.points].reverse();
                      return (
                      <TableRow key={lane.rank}>
                        <TableCell className="font-medium sticky left-0 z-10 bg-background">
                          {lane.rank}
                        </TableCell>
                        {pointsNewestFirst.map(pt => {
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
                          if (pt.unique_users != null) tooltipParts.push(`${pt.unique_users} users`);
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
                          const highlightIndex = pt.item != null ? selectedItems.indexOf(pt.item) : -1;
                          const highlightColor =
                            highlightIndex >= 0 ? CHART_COLORS[highlightIndex % CHART_COLORS.length] : undefined;
                          const hasItem = pt.item != null && pt.item !== '';
                          return (
                            <TableCell
                              key={pt.month}
                              className="whitespace-nowrap relative"
                              onClick={hasItem ? () => addItem(pt.item!) : undefined}
                              role={hasItem ? 'button' : undefined}
                              style={hasItem ? { cursor: 'pointer' } : undefined}
                            >
                              {highlightColor && (
                                <span
                                  className="absolute inset-0 pointer-events-none"
                                  style={{ backgroundColor: highlightColor, opacity: 0.12 }}
                                  aria-hidden
                                />
                              )}
                              <span className="relative">
                                {tooltipContent ? (
                                  <CellTooltip content={tooltipContent}>{cellContent}</CellTooltip>
                                ) : (
                                  cellContent
                                )}
                              </span>
                            </TableCell>
                          );
                        })}
                      </TableRow>
                    );
                    })}
                  </TableBody>
                </Table>
              </div>
              );
            })()}
          </CardContent>
        </Card>
      )}

      {series && viewMode === 'by-item' && (
        <>
          <Card className="mb-4">
            <CardHeader>
              <CardTitle>Rank over time</CardTitle>
              {chartData.length > 0 && (
                <div className="flex flex-wrap items-center gap-2 pt-2">
                  <Label className="text-sm font-normal text-muted-foreground shrink-0">
                    Chart metric
                  </Label>
                  <Tabs
                    value={chartPrimaryMetric}
                    onValueChange={v =>
                      setChartPrimaryMetric(v as 'rank' | 'shaves' | 'unique_users')
                    }
                  >
                    <TabsList className="h-8">
                      <TabsTrigger value="rank" className="text-xs px-2 py-1">
                        Rank
                      </TabsTrigger>
                      <TabsTrigger value="shaves" className="text-xs px-2 py-1">
                        Shaves
                      </TabsTrigger>
                      <TabsTrigger value="unique_users" className="text-xs px-2 py-1">
                        Unique users
                      </TabsTrigger>
                    </TabsList>
                  </Tabs>
                </div>
              )}
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
                        domain={
                          chartPrimaryMetric === 'rank'
                            ? [maxRank + 1, 1]
                            : [0, maxChartValue]
                        }
                        tick={{ fontSize: 12 }}
                        label={{
                          value:
                            chartPrimaryMetric === 'rank'
                              ? 'Rank (1 = top)'
                              : chartPrimaryMetric === 'shaves'
                                ? 'Shaves'
                                : 'Unique users',
                          angle: -90,
                          position: 'insideLeft',
                        }}
                      />
                      <Tooltip
                        content={(props) => RankChartTooltipContent(props, series.series)}
                      />
                      <Legend />
                      {series.series.map((entry, i) => {
                        const dataKey =
                          chartPrimaryMetric === 'rank'
                            ? entry.item
                            : chartPrimaryMetric === 'shaves'
                              ? `${entry.item}_shaves`
                              : `${entry.item}_unique_users`;
                        return (
                          <Line
                            key={entry.item}
                            type="monotone"
                            dataKey={dataKey}
                            stroke={CHART_COLORS[i % CHART_COLORS.length]}
                            strokeWidth={2}
                            dot={{ r: 3 }}
                            connectNulls={false}
                            name={entry.item}
                          />
                        );
                      })}
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
                            const uniqueUsers = row[`${entry.item}_unique_users`];
                            let cell: string;
                            if (rank === '' || rank === undefined) {
                              cell = '—';
                            } else {
                              const hasShaves = shaves !== '' && shaves !== undefined;
                              const hasUsers = uniqueUsers !== '' && uniqueUsers !== undefined;
                              if (hasShaves && hasUsers) {
                                cell = `#${rank} (${shaves} shaves, ${uniqueUsers} users)`;
                              } else if (hasShaves) {
                                cell = `#${rank} (${shaves})`;
                              } else if (hasUsers) {
                                cell = `#${rank} (${uniqueUsers} users)`;
                              } else {
                                cell = `#${rank}`;
                              }
                            }
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
