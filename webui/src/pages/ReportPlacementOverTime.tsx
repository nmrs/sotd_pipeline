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
  ReportRankingsTable,
  ReportRankingsSeriesResponse,
} from '@/services/api';
import { handleApiError } from '@/services/api';
import LoadingSpinner from '@/components/layout/LoadingSpinner';
import { ChevronDown, X } from 'lucide-react';

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

          {error && (
            <p className="text-sm text-destructive" role="alert">
              {error}
            </p>
          )}
        </CardContent>
      </Card>

      {series && (
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

      {!series && selectedTableId && selectedItems.length > 0 && !loadingSeries && !error && (
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
