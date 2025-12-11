import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Calendar as CalendarIcon, List as ListIcon, Table as TableIcon, BarChart3 as SummaryIcon, Loader2 } from 'lucide-react';
import { CommentDisplay } from '@/components/domain/CommentDisplay';
import CommentModal from '@/components/domain/CommentModal';
import { getCommentDetail, CommentDetail } from '@/services/api';
import { getProductsForMonth, getProductUsageAnalysis, getProductYearlySummary } from '@/services/api';
import { Product, ProductUsageAnalysis, ProductYearlySummary } from '@/types/productUsage';
import MonthSelector from '@/components/forms/MonthSelector';

const ProductUsage: React.FC = () => {
  const [selectedMonth, setSelectedMonth] = useState<string>('');
  const [selectedProductType, setSelectedProductType] = useState<'razor' | 'blade' | 'brush' | 'soap' | ''>('');
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [productSearch, setProductSearch] = useState<string>('');
  const [products, setProducts] = useState<Product[]>([]);
  const [filteredProducts, setFilteredProducts] = useState<Product[]>([]);
  const [productAnalysis, setProductAnalysis] = useState<ProductUsageAnalysis | null>(null);
  const [yearlySummary, setYearlySummary] = useState<ProductYearlySummary | null>(null);
  const [yearlySummaryLoading, setYearlySummaryLoading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [viewMode, setViewMode] = useState<'table' | 'calendar' | 'list' | 'summary'>('calendar');

  // Comment modal state
  const [selectedComment, setSelectedComment] = useState<CommentDetail | null>(null);
  const [commentModalOpen, setCommentModalOpen] = useState(false);
  const [commentLoading, setCommentLoading] = useState(false);
  const [allComments, setAllComments] = useState<CommentDetail[]>([]);
  const [currentCommentIndex, setCurrentCommentIndex] = useState<number>(0);
  const [remainingCommentIds, setRemainingCommentIds] = useState<string[]>([]);

  // Track expanded state for each user to synchronize comment IDs and usage dates
  const [expandedUsers, setExpandedUsers] = useState<Record<string, boolean>>({});

  // Fetch products when month and product type change
  useEffect(() => {
    if (selectedMonth && selectedProductType) {
      fetchProductsForMonth(selectedMonth, selectedProductType);
    } else {
      setProducts([]);
      setFilteredProducts([]);
      setSelectedProduct(null);
      setProductAnalysis(null);
      setYearlySummary(null);
    }
  }, [selectedMonth, selectedProductType]);

  // Filter products when search changes
  useEffect(() => {
    if (productSearch.trim() === '') {
      setFilteredProducts(products);
    } else {
      const searchLower = productSearch.toLowerCase();
      const filtered = products.filter(
        p =>
          p.brand.toLowerCase().includes(searchLower) ||
          p.model.toLowerCase().includes(searchLower)
      );
      setFilteredProducts(filtered);
    }
  }, [productSearch, products]);

  const fetchProductsForMonth = async (month: string, productType: string) => {
    try {
      setLoading(true);
      setError('');
      const productsData = await getProductsForMonth(month, productType);
      setProducts(productsData);
      setFilteredProducts(productsData);
      setSelectedProduct(null);
      setProductAnalysis(null);
    } catch (err) {
      setError('Failed to fetch products for month');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchProductAnalysis = async (month: string, productType: string, product: Product) => {
    try {
      setLoading(true);
      setError('');
      const analysis = await getProductUsageAnalysis(month, productType, product.brand, product.model);
      setProductAnalysis(analysis);
    } catch (err) {
      setError('Failed to fetch product usage analysis');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchYearlySummary = async (month: string, productType: string, product: Product) => {
    try {
      setYearlySummaryLoading(true);
      setError('');
      const summary = await getProductYearlySummary(month, productType, product.brand, product.model);
      setYearlySummary(summary);
    } catch (err) {
      setError('Failed to fetch yearly summary');
      console.error(err);
    } finally {
      setYearlySummaryLoading(false);
    }
  };

  // Comment modal handlers
  const handleCommentClick = async (commentId: string, allCommentIds?: string[]) => {
    try {
      setCommentLoading(true);

      // Always load just the clicked comment initially for fast response
      const comment = await getCommentDetail(commentId, [selectedMonth]);
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
      setError('Failed to load comment details');
    } finally {
      setCommentLoading(false);
    }
  };

  const handleCommentNavigation = async (direction: 'prev' | 'next') => {
    if (direction === 'prev' && currentCommentIndex > 0) {
      setCurrentCommentIndex(currentCommentIndex - 1);
      setSelectedComment(allComments[currentCommentIndex - 1]);
    } else if (direction === 'next') {
      if (currentCommentIndex < allComments.length - 1) {
        setCurrentCommentIndex(currentCommentIndex + 1);
        setSelectedComment(allComments[currentCommentIndex + 1]);
      } else if (remainingCommentIds.length > 0) {
        // Load next comment from remaining IDs
        const nextCommentId = remainingCommentIds[0];
        try {
          setCommentLoading(true);
          const nextComment = await getCommentDetail(nextCommentId, [selectedMonth]);
          setAllComments([...allComments, nextComment]);
          setRemainingCommentIds(remainingCommentIds.slice(1));
          setCurrentCommentIndex(allComments.length);
          setSelectedComment(nextComment);
        } catch (err: unknown) {
          console.error('Error loading next comment:', err);
          setError('Failed to load next comment');
        } finally {
          setCommentLoading(false);
        }
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

  const handleMonthChange = (month: string) => {
    setSelectedMonth(month);
    setSelectedProduct(null);
    setProductAnalysis(null);
    setYearlySummary(null);
    setProductSearch('');
  };

  const handleProductTypeChange = (productType: string) => {
    setSelectedProductType(productType as 'razor' | 'blade' | 'brush' | 'soap' | '');
    setSelectedProduct(null);
    setProductAnalysis(null);
    setYearlySummary(null);
    setProductSearch('');
  };

  const handleProductSelect = (product: Product) => {
    setSelectedProduct(product);
    if (selectedMonth && selectedProductType) {
      fetchProductAnalysis(selectedMonth, selectedProductType, product);
      fetchYearlySummary(selectedMonth, selectedProductType, product);
    }
  };

  const handleUserExpandChange = (username: string, expanded: boolean) => {
    setExpandedUsers(prev => ({
      ...prev,
      [username]: expanded,
    }));
  };

  const renderTableView = () => {
    if (!productAnalysis) {
      return (
        <div className='flex items-center justify-center h-64 text-muted-foreground'>
          Select a product to see usage analysis
        </div>
      );
    }

    return (
      <div className='overflow-x-auto'>
        <table className='w-full border-collapse border border-border'>
          <thead>
            <tr className='bg-muted'>
              <th className='border border-border p-2 text-center'>#</th>
              <th className='border border-border p-2 text-left'>Username</th>
              <th className='border border-border p-2 text-center'>Usage Count</th>
              <th className='border border-border p-2 text-left'>Usage Dates</th>
              <th className='border border-border p-2 text-left'>Comment IDs</th>
            </tr>
          </thead>
          <tbody>
            {productAnalysis.users.map((user, index) => (
              <tr key={user.username} className='hover:bg-muted/50'>
                <td className='border border-border p-2 text-center font-medium'>{index + 1}</td>
                <td className='border border-border p-2'>{user.username}</td>
                <td className='border border-border p-2 text-center'>{user.usage_count}</td>
                <td className='border border-border p-2'>
                  <CommentDisplay
                    commentIds={user.comment_ids}
                    onCommentClick={commentId => handleCommentClick(commentId, user.comment_ids)}
                    displayMode='dates'
                    dates={user.usage_dates}
                    expanded={expandedUsers[user.username]}
                    onExpandChange={expanded => handleUserExpandChange(user.username, expanded)}
                  />
                </td>
                <td className='border border-border p-2'>
                  <CommentDisplay
                    commentIds={user.comment_ids}
                    onCommentClick={commentId => handleCommentClick(commentId, user.comment_ids)}
                    expanded={expandedUsers[user.username]}
                    onExpandChange={expanded => handleUserExpandChange(user.username, expanded)}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderCalendarView = () => {
    if (!productAnalysis) {
      return (
        <div className='flex items-center justify-center h-64 text-muted-foreground'>
          Select a product to see usage analysis
        </div>
      );
    }

    // Parse the month to get year and month number
    const [year, month] = selectedMonth.split('-').map(Number);
    const startDate = new Date(year, month - 1, 1);
    const endDate = new Date(year, month, 0);
    const daysInMonth = endDate.getDate();

    // Create array of dates for the month
    const dates = Array.from({ length: daysInMonth }, (_, i) => i + 1);

    // Convert usage dates to day numbers for easy lookup
    const usageDays = new Set(
      Object.keys(productAnalysis.comments_by_date).map(dateStr => {
        const date = new Date(dateStr + 'T00:00:00'); // Add time to avoid timezone issues
        return date.getDate();
      })
    );

    // Get users who used the product on each date for distinct user count
    const dateUserMap: Record<string, string[]> = {};
    productAnalysis.users.forEach(user => {
      user.usage_dates.forEach(date => {
        if (!dateUserMap[date]) {
          dateUserMap[date] = [];
        }
        if (!dateUserMap[date].includes(user.username)) {
          dateUserMap[date].push(user.username);
        }
      });
    });

    return (
      <div className='space-y-4'>
        <div className='text-center'>
          <h3 className='text-lg font-semibold'>
            {new Date(year, month - 1).toLocaleDateString('en-US', {
              month: 'long',
              year: 'numeric',
            })}
          </h3>
          <p className='text-sm text-muted-foreground'>
            Total Usage: {productAnalysis.total_usage} times by {productAnalysis.unique_users} users
          </p>
        </div>

        <div className='grid grid-cols-7 gap-1'>
          {/* Day headers */}
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
            <div key={day} className='p-2 text-center text-sm font-medium text-muted-foreground'>
              {day}
            </div>
          ))}

          {/* Empty cells for days before month starts */}
          {Array.from({ length: startDate.getDay() }, (_, i) => (
            <div key={`empty-${i}`} className='p-2' />
          ))}

          {/* Month days */}
          {dates.map(day => {
            const isUsed = usageDays.has(day);
            const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            const dayCommentIds = productAnalysis.comments_by_date[dateStr] || [];
            const dayUsers = dateUserMap[dateStr] || [];
            const dailyUses = dayCommentIds.length;
            const distinctUsers = dayUsers.length;

            return (
              <div
                key={day}
                className={`p-2 text-center border rounded-md min-h-[80px] flex flex-col items-center justify-center ${
                  isUsed
                    ? 'bg-green-100 border-green-300 text-green-800'
                    : 'bg-gray-100 border-gray-300 text-gray-400'
                }`}
              >
                <span className='text-sm font-medium'>{day}</span>
                {isUsed && dailyUses > 0 && (
                  <div className='mt-1 space-y-0.5'>
                    <div className='text-xs'>
                      {dailyUses} {dailyUses === 1 ? 'use' : 'uses'}
                    </div>
                    <div className='text-xs'>
                      {distinctUsers} {distinctUsers === 1 ? 'user' : 'users'}
                    </div>
                    <div className='mt-1'>
                      <CommentDisplay
                        commentIds={dayCommentIds}
                        onCommentClick={commentId => handleCommentClick(commentId, dayCommentIds)}
                      />
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderListView = () => {
    if (!productAnalysis) {
      return (
        <div className='flex items-center justify-center h-64 text-muted-foreground'>
          Select a product to see usage analysis
        </div>
      );
    }

    const [year, month] = selectedMonth.split('-').map(Number);
    const daysInMonth = new Date(year, month, 0).getDate();
    const usageDays = new Set(
      Object.keys(productAnalysis.comments_by_date).map(dateStr => {
        const date = new Date(dateStr + 'T00:00:00'); // Add time to avoid timezone issues
        return date.getDate();
      })
    );

    // Get users who used the product on each date
    const dateUserMap: Record<string, string[]> = {};
    productAnalysis.users.forEach(user => {
      user.usage_dates.forEach(date => {
        if (!dateUserMap[date]) {
          dateUserMap[date] = [];
        }
        if (!dateUserMap[date].includes(user.username)) {
          dateUserMap[date].push(user.username);
        }
      });
    });

    return (
      <div className='space-y-4'>
        <div className='text-center mb-4'>
          <h3 className='text-lg font-semibold'>
            {new Date(year, month - 1).toLocaleDateString('en-US', {
              month: 'long',
              year: 'numeric',
            })}
          </h3>
          <p className='text-sm text-muted-foreground'>
            Total Usage: {productAnalysis.total_usage} times by {productAnalysis.unique_users} users
          </p>
        </div>

        <div className='space-y-2'>
          {Array.from({ length: daysInMonth }, (_, i) => {
            const day = i + 1;
            const isUsed = usageDays.has(day);
            const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            const dayCommentIds = productAnalysis.comments_by_date[dateStr] || [];
            const dayUsers = dateUserMap[dateStr] || [];

            const dailyUses = dayCommentIds.length;
            const distinctUsers = dayUsers.length;

            return (
              <div
                key={day}
                className={`flex items-center justify-between p-3 border rounded-lg ${
                  isUsed ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'
                }`}
              >
                <div className='flex items-center space-x-3'>
                  <span className='font-medium'>Day {day}</span>
                  <Badge variant={isUsed ? 'default' : 'outline'} className={isUsed ? 'bg-green-600' : ''}>
                    {isUsed ? 'Used' : 'Not Used'}
                  </Badge>
                  {isUsed && (
                    <div className='flex items-center space-x-2 text-sm'>
                      <Badge variant='outline' className='bg-blue-50'>
                        {dailyUses} {dailyUses === 1 ? 'use' : 'uses'}
                      </Badge>
                      <Badge variant='outline' className='bg-purple-50'>
                        {distinctUsers} {distinctUsers === 1 ? 'user' : 'users'}
                      </Badge>
                      {dayUsers.length > 0 && (
                        <span className='text-muted-foreground'>
                          ({dayUsers.join(', ')})
                        </span>
                      )}
                    </div>
                  )}
                </div>
                {isUsed && dayCommentIds.length > 0 && (
                  <div className='text-sm text-muted-foreground'>
                    <CommentDisplay
                      commentIds={dayCommentIds}
                      onCommentClick={commentId => handleCommentClick(commentId, dayCommentIds)}
                    />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderSummaryView = () => {
    if (!yearlySummary) {
      return (
        <div className='text-center p-8 text-muted-foreground'>
          {yearlySummaryLoading ? (
            <div className='flex items-center justify-center'>
              <Loader2 className='h-8 w-8 animate-spin mr-2' />
              <span>Loading yearly summary...</span>
            </div>
          ) : (
            <span>No yearly summary data available</span>
          )}
        </div>
      );
    }

    return (
      <div className='space-y-4'>
        <div className='text-center mb-4'>
          <h3 className='text-lg font-semibold'>
            Yearly Summary: {yearlySummary.product.brand} {yearlySummary.product.model}
          </h3>
          <p className='text-sm text-muted-foreground'>Past 12 Months</p>
        </div>

        <div className='overflow-x-auto'>
          <table className='w-full border-collapse border border-border'>
            <thead>
              <tr className='bg-muted'>
                <th className='border border-border p-2 text-left'>Month</th>
                <th className='border border-border p-2 text-center'>Shaves</th>
                <th className='border border-border p-2 text-center'>Unique Users</th>
                <th className='border border-border p-2 text-center'>Rank</th>
              </tr>
            </thead>
            <tbody>
              {yearlySummary.months.map(monthData => {
                // Format month for display (e.g., "Nov 2025")
                const [year, month] = monthData.month.split('-');
                const monthDate = new Date(parseInt(year), parseInt(month) - 1, 1);
                const monthDisplay = monthDate.toLocaleDateString('en-US', {
                  month: 'short',
                  year: 'numeric',
                });

                return (
                  <tr
                    key={monthData.month}
                    className={`hover:bg-muted/50 ${
                      monthData.month === selectedMonth ? 'bg-blue-50' : ''
                    }`}
                  >
                    <td className='border border-border p-2 font-medium'>{monthDisplay}</td>
                    <td className='border border-border p-2 text-center'>
                      {monthData.has_data ? monthData.shaves.toLocaleString() : '-'}
                    </td>
                    <td className='border border-border p-2 text-center'>
                      {monthData.has_data ? monthData.unique_users.toLocaleString() : '-'}
                    </td>
                    <td className='border border-border p-2 text-center'>
                      {monthData.has_data && monthData.rank !== null
                        ? monthData.rank.toLocaleString()
                        : '-'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  return (
    <div className='container mx-auto p-6 space-y-6'>
      <div className='flex items-center justify-between'>
        <div>
          <h1 className='text-3xl font-bold'>Product Usage</h1>
          <p className='text-muted-foreground'>Analyze which users used a specific product in any month</p>
        </div>
      </div>

      {/* Month, Product Type, and Product Selection */}
      <Card>
        <CardHeader>
          <CardTitle>Select Month, Product Type, and Product</CardTitle>
        </CardHeader>
        <CardContent className='space-y-4'>
          {/* Month Selection */}
          <div className='space-y-2'>
            <Label htmlFor='month'>Month</Label>
            <MonthSelector
              selectedMonths={selectedMonth ? [selectedMonth] : []}
              onMonthsChange={months => handleMonthChange(months[0] || '')}
              multiple={false}
              label=''
            />
          </div>

          {/* Product Type Selection */}
          {selectedMonth && (
            <div className='space-y-2'>
              <Label htmlFor='product-type'>Product Type</Label>
              <Select value={selectedProductType} onValueChange={handleProductTypeChange}>
                <SelectTrigger id='product-type'>
                  <SelectValue placeholder='Select product type' />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value='razor'>Razor</SelectItem>
                  <SelectItem value='blade'>Blade</SelectItem>
                  <SelectItem value='brush'>Brush</SelectItem>
                  <SelectItem value='soap'>Soap</SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}

          {/* Product Selection */}
          {selectedMonth && selectedProductType && (
            <div className='space-y-2'>
              <Label htmlFor='product'>Product</Label>
              <div className='flex space-x-2'>
                <Input
                  id='product'
                  placeholder='Search for a product...'
                  value={productSearch}
                  onChange={e => setProductSearch(e.target.value)}
                  className='flex-1'
                />
              </div>

              {/* Product Suggestions */}
              {loading ? (
                <div className='flex items-center justify-center p-4'>
                  <Loader2 className='h-4 w-4 animate-spin' />
                </div>
              ) : filteredProducts.length > 0 ? (
                <div className='mt-2 space-y-1 max-h-60 overflow-y-auto'>
                  {filteredProducts.slice(0, 20).map(product => (
                    <div
                      key={product.key}
                      className='flex items-center justify-between p-2 hover:bg-muted rounded cursor-pointer'
                      onClick={() => handleProductSelect(product)}
                    >
                      <span>
                        {product.brand} {product.model}
                      </span>
                      <div className='flex items-center space-x-2'>
                        <Badge variant='outline'>{product.usage_count} uses</Badge>
                        <Badge variant='outline'>{product.unique_users} users</Badge>
                      </div>
                    </div>
                  ))}
                  {filteredProducts.length > 20 && (
                    <div className='text-sm text-muted-foreground text-center'>
                      +{filteredProducts.length - 20} more products
                    </div>
                  )}
                </div>
              ) : (
                <div className='text-sm text-muted-foreground text-center p-4'>
                  No products found
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Card className='border-destructive'>
          <CardContent className='pt-6'>
            <div className='text-destructive text-center'>{error}</div>
          </CardContent>
        </Card>
      )}

      {/* Analysis Results */}
      {productAnalysis && (
        <Card>
          <CardHeader>
            <div className='flex items-center justify-between'>
              <CardTitle>
                Usage Analysis for {productAnalysis.product.brand} {productAnalysis.product.model} -{' '}
                {selectedMonth}
              </CardTitle>

              {/* View Toggle */}
              <div className='flex items-center space-x-2'>
                <Button
                  variant={viewMode === 'calendar' ? 'default' : 'outline'}
                  size='sm'
                  onClick={() => setViewMode('calendar')}
                >
                  <CalendarIcon className='h-4 w-4 mr-2' />
                  Calendar
                </Button>
                <Button
                  variant={viewMode === 'table' ? 'default' : 'outline'}
                  size='sm'
                  onClick={() => setViewMode('table')}
                >
                  <TableIcon className='h-4 w-4 mr-2' />
                  Table
                </Button>
                <Button
                  variant={viewMode === 'list' ? 'default' : 'outline'}
                  size='sm'
                  onClick={() => setViewMode('list')}
                >
                  <ListIcon className='h-4 w-4 mr-2' />
                  List
                </Button>
                <Button
                  variant={viewMode === 'summary' ? 'default' : 'outline'}
                  size='sm'
                  onClick={() => setViewMode('summary')}
                >
                  <SummaryIcon className='h-4 w-4 mr-2' />
                  Summary
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className='flex items-center justify-center h-64'>
                <Loader2 className='h-8 w-8 animate-spin' />
              </div>
            ) : (
              <div>
                {viewMode === 'table' && renderTableView()}
                {viewMode === 'calendar' && renderCalendarView()}
                {viewMode === 'list' && renderListView()}
                {viewMode === 'summary' && (
                  yearlySummaryLoading ? (
                    <div className='flex items-center justify-center h-64'>
                      <Loader2 className='h-8 w-8 animate-spin' />
                    </div>
                  ) : (
                    renderSummaryView()
                  )
                )}
              </div>
            )}
          </CardContent>
        </Card>
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

export default ProductUsage;

