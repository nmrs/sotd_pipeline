import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Calendar as CalendarIcon, List as ListIcon, Loader2, Copy, Check } from 'lucide-react';
import { CommentDisplay } from '@/components/domain/CommentDisplay';
import CommentModal from '@/components/domain/CommentModal';
import { getCommentDetail, CommentDetail } from '@/services/api';
import MonthSelector from '@/components/forms/MonthSelector';
import axios from 'axios';

interface UserData {
  username: string;
  post_count: number;
}

interface UserPostingAnalysis {
  user: string;
  posted_days: number;
  missed_days: number;
  posted_dates: string[];
  comment_ids: string[];
  comments_by_date: Record<string, string[]>;
  // Product usage data
  razors: Array<{
    key: string;
    brand: string;
    model: string;
    count: number;
    comment_ids: string[];
  }>;
  blades: Array<{
    key: string;
    brand: string;
    model: string;
    count: number;
    comment_ids: string[];
  }>;
  brushes: Array<{
    key: string;
    brand: string;
    model: string;
    handle_brand: string;
    knot_brand: string;
    knot_model: string;
    count: number;
    comment_ids: string[];
  }>;
  soaps: Array<{
    key: string;
    brand: string;
    model: string;
    count: number;
    comment_ids: string[];
  }>;
}

const MonthlyUserPosts: React.FC = () => {
  const [selectedMonths, setSelectedMonths] = useState<string[]>([]);
  const [selectedUser, setSelectedUser] = useState<string>('');
  const [users, setUsers] = useState<UserData[]>([]);
  const [userAnalyses, setUserAnalyses] = useState<Array<{ month: string; analysis: UserPostingAnalysis }>>([]);
  const [aggregatedAnalysis, setAggregatedAnalysis] = useState<UserPostingAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [viewMode, setViewMode] = useState<'calendar' | 'list'>('calendar');

  // Comment modal state
  const [selectedComment, setSelectedComment] = useState<CommentDetail | null>(null);
  const [commentModalOpen, setCommentModalOpen] = useState(false);
  const [commentLoading, setCommentLoading] = useState(false);
  const [allComments, setAllComments] = useState<CommentDetail[]>([]);
  const [currentCommentIndex, setCurrentCommentIndex] = useState<number>(0);
  const [remainingCommentIds, setRemainingCommentIds] = useState<string[]>([]);

  // Track expanded state for each product to synchronize comment IDs and usage dates
  const [expandedProducts, setExpandedProducts] = useState<Record<string, boolean>>({});

  // Copy to markdown state
  const [copyLoading, setCopyLoading] = useState<Record<string, boolean>>({});
  const [copySuccess, setCopySuccess] = useState<Record<string, boolean>>({});

  // Fetch users when selected months change
  useEffect(() => {
    if (selectedMonths.length > 0) {
      fetchUsersForMonths(selectedMonths);
    }
  }, [selectedMonths]);

  const fetchUsersForMonths = async (months: string[]) => {
    try {
      setLoading(true);
      const responses = await Promise.all(
        months.map(month => axios.get(`/api/monthly-user-posts/users/${month}`))
      );

      // Merge users across all months
      const userMap = new Map<string, number>();
      responses.forEach(response => {
        response.data.forEach((user: UserData) => {
          const current = userMap.get(user.username) || 0;
          userMap.set(user.username, current + user.post_count);
        });
      });

      const mergedUsers = Array.from(userMap.entries()).map(([username, post_count]) => ({
        username,
        post_count,
      }));

      setUsers(mergedUsers.sort((a, b) => b.post_count - a.post_count));
    } catch (err) {
      setError('Failed to fetch users for months');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const aggregateUserAnalyses = (analyses: UserPostingAnalysis[]): UserPostingAnalysis => {
    // Combine posted dates
    const allPostedDates = new Set<string>();
    analyses.forEach(a => a.posted_dates.forEach(d => allPostedDates.add(d)));

    // Merge comments_by_date
    const mergedCommentsByDate: Record<string, string[]> = {};
    analyses.forEach(a => {
      Object.entries(a.comments_by_date).forEach(([date, ids]) => {
        if (!mergedCommentsByDate[date]) {
          mergedCommentsByDate[date] = [];
        }
        mergedCommentsByDate[date].push(...ids);
      });
    });

    // Aggregate products
    const aggregateProducts = (productArrays: Array<Array<any>>) => {
      const productMap = new Map<string, any>();
      productArrays.forEach(products => {
        products.forEach(product => {
          const existing = productMap.get(product.key);
          if (existing) {
            existing.count += product.count;
            existing.comment_ids = [...new Set([...existing.comment_ids, ...product.comment_ids])];
          } else {
            productMap.set(product.key, {
              ...product,
              comment_ids: [...product.comment_ids],
            });
          }
        });
      });
      return Array.from(productMap.values()).sort((a, b) => b.count - a.count);
    };

    return {
      user: analyses[0].user,
      posted_days: analyses.reduce((sum, a) => sum + a.posted_days, 0),
      missed_days: analyses.reduce((sum, a) => sum + a.missed_days, 0),
      posted_dates: Array.from(allPostedDates).sort(),
      comment_ids: [...new Set(analyses.flatMap(a => a.comment_ids))],
      comments_by_date: mergedCommentsByDate,
      razors: aggregateProducts(analyses.map(a => a.razors)),
      blades: aggregateProducts(analyses.map(a => a.blades)),
      brushes: aggregateProducts(analyses.map(a => a.brushes)),
      soaps: aggregateProducts(analyses.map(a => a.soaps)),
    };
  };

  const fetchUserAnalyses = async (months: string[], username: string) => {
    try {
      setLoading(true);
      const responses = await Promise.all(
        months.map(month =>
          axios
            .get(`/api/monthly-user-posts/analysis/${month}/${username}`)
            .catch(err => {
              // Handle case where user doesn't exist in a month
              if (err.response?.status === 404) return null;
              throw err;
            })
        )
      );      const validAnalysesWithMonths = responses
        .map((r, index) => (r !== null ? { month: months[index], analysis: r.data } : null))
        .filter((r): r is { month: string; analysis: UserPostingAnalysis } => r !== null);      if (validAnalysesWithMonths.length === 0) {
        setError(`User ${username} not found in any selected month`);
        setAggregatedAnalysis(null);
        setUserAnalyses([]);
        return;
      }

      // Aggregate analyses
      const validAnalyses = validAnalysesWithMonths.map(item => item.analysis);      const aggregated = aggregateUserAnalyses(validAnalyses);      setAggregatedAnalysis(aggregated);
      setUserAnalyses(validAnalysesWithMonths);    } catch (err) {      const errorMessage = err instanceof Error && 'response' in err && (err as any).response?.status === 500
        ? 'Server error: Failed to fetch user analysis. Please try again later.'
        : err instanceof Error
        ? `Failed to fetch user analysis: ${err.message}`
        : 'Failed to fetch user analysis';
      setError(errorMessage);
      setAggregatedAnalysis(null);
      setUserAnalyses([]);
      console.error('[MonthlyUserPosts] Error fetching user analysis:', err);
    } finally {
      setLoading(false);
    }
  };

  // Comment modal handlers
  const handleCommentClick = async (commentId: string, allCommentIds?: string[]) => {
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
      setError('Failed to load comment details');
    } finally {
      setCommentLoading(false);
    }
  };

  // Helper function to extract usage dates for a product
  const getProductUsageDates = (commentIds: string[]): string[] => {
    if (!aggregatedAnalysis || !commentIds || commentIds.length === 0) {
      return [];
    }

    const usageDates: string[] = [];
    const commentsByDate = aggregatedAnalysis.comments_by_date;

    // For each comment ID, find which date it corresponds to
    commentIds.forEach(commentId => {
      for (const [date, dateCommentIds] of Object.entries(commentsByDate)) {
        if (dateCommentIds.includes(commentId)) {
          usageDates.push(date);
          break;
        }
      }
    });

    return usageDates.sort(); // Sort dates chronologically
  };

  // Helper function to generate unique product keys
  const getProductKey = (productType: string, product: any): string => {
    switch (productType) {
      case 'razor':
        return `razor_${product.brand}_${product.model}`;
      case 'blade':
        return `blade_${product.brand}_${product.model}`;
      case 'brush':
        return `brush_${product.brand}_${product.knot_model || 'unknown'}`;
      case 'soap':
        return `soap_${product.brand}_${product.model}`;
      default:
        return `unknown_${productType}_${JSON.stringify(product)}`;
    }
  };

  // Helper function to handle expand/collapse state changes
  const handleProductExpandChange = (productKey: string, expanded: boolean) => {
    setExpandedProducts(prev => ({
      ...prev,
      [productKey]: expanded,
    }));
  };

  // Helper function to fetch comment URLs
  const getCommentUrls = async (
    commentIds: string[],
    months: string[]
  ): Promise<Record<string, string>> => {
    const urlMap: Record<string, string> = {};
    const uniqueIds = [...new Set(commentIds)];

    // Fetch URLs in parallel
    const promises = uniqueIds.map(async commentId => {
      try {
        const comment = await getCommentDetail(commentId, months);
        return { commentId, url: comment.url };
      } catch (err) {
        console.warn(`Failed to fetch URL for comment ${commentId}:`, err);
        return { commentId, url: '' };
      }
    });

    const results = await Promise.all(promises);
    results.forEach(({ commentId, url }) => {
      urlMap[commentId] = url;
    });

    return urlMap;
  };

  // Helper function to copy text to clipboard
  const copyToClipboard = async (text: string): Promise<boolean> => {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
      return false;
    }
  };

  // Generate markdown for calendar view
  const generateCalendarMarkdown = async (
    month: string,
    monthAnalysis: UserPostingAnalysis,
    year: number,
    monthNum: number,
    selectedMonths: string[]
  ): Promise<string> => {
    const startDate = new Date(year, monthNum - 1, 1);
    const endDate = new Date(year, monthNum, 0);
    const daysInMonth = endDate.getDate();
    const firstDayOfWeek = startDate.getDay();

    // Collect all unique comment IDs for this month
    const allCommentIds = new Set<string>();
    Object.values(monthAnalysis.comments_by_date).forEach(ids => {
      ids.forEach(id => allCommentIds.add(id));
    });

    // Fetch URLs for all comment IDs
    const commentUrls = await getCommentUrls(Array.from(allCommentIds), selectedMonths);

    // Build calendar grid
    const monthName = new Date(year, monthNum - 1).toLocaleDateString('en-US', {
      month: 'long',
      year: 'numeric',
    });

    let markdown = `## ${monthName}\n\n`;
    markdown += '| Sun | Mon | Tue | Wed | Thu | Fri | Sat |\n';
    markdown += '|-----|-----|-----|-----|-----|-----|-----|\n';

    // Empty cells for days before month starts
    const emptyCells = Array(firstDayOfWeek).fill('|     ');
    let currentRow = emptyCells.join('');

    // Generate calendar days
    for (let day = 1; day <= daysInMonth; day++) {
      const dateStr = `${year}-${String(monthNum).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      const dayCommentIds = monthAnalysis.comments_by_date[dateStr] || [];
      const isPosted = dayCommentIds.length > 0;

      if (isPosted && dayCommentIds.length > 0) {
        // Use the first comment URL for the day link
        const firstCommentId = dayCommentIds[0];
        const url = commentUrls[firstCommentId] || '';
        if (url) {
          currentRow += `| [${day}](${url}) `;
        } else {
          currentRow += `| ${day} `;
        }
      } else {
        currentRow += `| ${day} `;
      }

      // Start new row on Saturday
      if ((firstDayOfWeek + day) % 7 === 0) {
        markdown += currentRow + '|\n';
        currentRow = '';
      }
    }

    // Add remaining cells for the last row
    if (currentRow) {
      const remainingCells = 7 - (currentRow.match(/\|/g) || []).length;
      for (let i = 0; i < remainingCells; i++) {
        currentRow += '|     ';
      }
      markdown += currentRow + '|\n';
    }

    return markdown;
  };

  // Generate markdown for list view
  const generateListViewMarkdown = (
    selectedMonths: string[],
    userAnalyses: Array<{ month: string; analysis: UserPostingAnalysis }>,
    aggregatedAnalysis: UserPostingAnalysis,
    singleMonth?: string
  ): string => {
    let markdown = '';

    // If singleMonth is specified, only generate for that month
    const monthsToProcess = singleMonth ? [singleMonth] : selectedMonths;

    if (selectedMonths.length > 1 && aggregatedAnalysis && !singleMonth) {
      markdown += `## ${selectedMonths.length} months selected\n\n`;
      markdown += `Posted: ${aggregatedAnalysis.posted_days} days, Missed: ${aggregatedAnalysis.missed_days} days\n\n`;
    }

    // Generate table for each month
    monthsToProcess.forEach(month => {
      const monthData = userAnalyses.find(a => a.month === month);
      const monthAnalysis = monthData?.analysis;

      if (!monthAnalysis) return;

      const [year, monthNum] = month.split('-').map(Number);
      const monthName = new Date(year, monthNum - 1).toLocaleDateString('en-US', {
        month: 'long',
        year: 'numeric',
      });

      markdown += `## ${monthName} - Daily Posting\n\n`;
      markdown += '| Date | Status |\n';
      markdown += '|------|--------|\n';

      const endDate = new Date(year, monthNum, 0);
      const daysInMonth = endDate.getDate();

      for (let day = 1; day <= daysInMonth; day++) {
        const dateStr = `${year}-${String(monthNum).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        const isPosted = monthAnalysis.posted_dates.includes(dateStr);
        const status = isPosted ? 'Posted' : 'Missed';

        markdown += `| ${dateStr} | ${status} |\n`;
      }

      markdown += '\n';
    });

    return markdown;
  };

  // Helper function to get dates with URLs for a product
  const getProductUsageDatesWithUrls = async (
    commentIds: string[],
    aggregatedAnalysis: UserPostingAnalysis,
    selectedMonths: string[]
  ): Promise<Array<{ date: string; url: string }>> => {
    if (!aggregatedAnalysis || !commentIds || commentIds.length === 0) {
      return [];
    }

    // Map comment IDs to dates
    const commentIdToDate: Record<string, string> = {};
    const commentsByDate = aggregatedAnalysis.comments_by_date;

    commentIds.forEach(commentId => {
      for (const [date, dateCommentIds] of Object.entries(commentsByDate)) {
        if (dateCommentIds.includes(commentId)) {
          commentIdToDate[commentId] = date;
          break;
        }
      }
    });

    // Fetch URLs for all comment IDs
    const commentUrls = await getCommentUrls(commentIds, selectedMonths);

    // Group by date and get first URL for each date
    const dateToUrl: Record<string, string> = {};
    commentIds.forEach(commentId => {
      const date = commentIdToDate[commentId];
      if (date && !dateToUrl[date]) {
        dateToUrl[date] = commentUrls[commentId] || '';
      }
    });

    // Create array of date-url pairs, sorted by date
    const datesWithUrls = Object.keys(dateToUrl)
      .sort()
      .map(date => ({
        date,
        url: dateToUrl[date],
      }));

    return datesWithUrls;
  };

  // Generate markdown for product aggregation tables
  const generateProductTableMarkdown = async (
    products: Array<{
      brand: string;
      model: string;
      count: number;
      comment_ids: string[];
      handle_brand?: string;
      knot_brand?: string;
      knot_model?: string;
    }>,
    productType: string,
    aggregatedAnalysis: UserPostingAnalysis,
    selectedMonths: string[]
  ): Promise<string> => {
    const productTypeName = productType.charAt(0).toUpperCase() + productType.slice(1);
    let markdown = `## ${productTypeName}s Used\n\n`;
    
    // For brushes, include handle and knot information
    if (productType === 'brush') {
      markdown += '| # | Brand | Model | Handle Brand | Knot Brand | Knot Model | Count | Dates |\n';
      markdown += '|---|-------|-------|-------------|------------|------------|-------|-------|\n';

      for (const [index, product] of products.entries()) {
        const datesWithUrls = await getProductUsageDatesWithUrls(
          product.comment_ids,
          aggregatedAnalysis,
          selectedMonths
        );
        const datesStr =
          datesWithUrls.length > 0
            ? datesWithUrls
                .map(({ date, url }) => (url ? `[${date}](${url})` : date))
                .join(', ')
            : '-';
        const handleBrand = product.handle_brand || '-';
        const knotBrand = product.knot_brand || '-';
        const knotModel = product.knot_model || '-';

        markdown += `| ${index + 1} | ${product.brand} | ${product.model} | ${handleBrand} | ${knotBrand} | ${knotModel} | ${product.count} | ${datesStr} |\n`;
      }
    } else if (productType === 'soap') {
      // For soaps, use "Scent" instead of "Model" to match the React view
      markdown += '| # | Brand | Scent | Count | Dates |\n';
      markdown += '|---|-------|-------|-------|-------|\n';

      for (const [index, product] of products.entries()) {
        const datesWithUrls = await getProductUsageDatesWithUrls(
          product.comment_ids,
          aggregatedAnalysis,
          selectedMonths
        );
        const datesStr =
          datesWithUrls.length > 0
            ? datesWithUrls
                .map(({ date, url }) => (url ? `[${date}](${url})` : date))
                .join(', ')
            : '-';

        markdown += `| ${index + 1} | ${product.brand} | ${product.model} | ${product.count} | ${datesStr} |\n`;
      }
    } else {
      markdown += '| # | Brand | Model | Count | Dates |\n';
      markdown += '|---|-------|-------|-------|-------|\n';

      for (const [index, product] of products.entries()) {
        const datesWithUrls = await getProductUsageDatesWithUrls(
          product.comment_ids,
          aggregatedAnalysis,
          selectedMonths
        );
        const datesStr =
          datesWithUrls.length > 0
            ? datesWithUrls
                .map(({ date, url }) => (url ? `[${date}](${url})` : date))
                .join(', ')
            : '-';

        markdown += `| ${index + 1} | ${product.brand} | ${product.model} | ${product.count} | ${datesStr} |\n`;
      }
    }

    return markdown;
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
          const nextComment = await getCommentDetail(nextCommentId, selectedMonths);
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

  // Handler for copying calendar markdown
  const handleCopyCalendarMarkdown = async (month: string) => {
    const monthData = userAnalyses.find(a => a.month === month);
    const monthAnalysis = monthData?.analysis;

    if (!monthAnalysis) return;

    const [year, monthNum] = month.split('-').map(Number);
    const key = `calendar-${month}`;

    setCopyLoading(prev => ({ ...prev, [key]: true }));
    setCopySuccess(prev => ({ ...prev, [key]: false }));

    try {
      const markdown = await generateCalendarMarkdown(
        month,
        monthAnalysis,
        year,
        monthNum,
        selectedMonths
      );
      const success = await copyToClipboard(markdown);

      if (success) {
        setCopySuccess(prev => ({ ...prev, [key]: true }));
        setTimeout(() => {
          setCopySuccess(prev => ({ ...prev, [key]: false }));
        }, 2000);
      }
    } catch (err) {
      console.error('Failed to generate calendar markdown:', err);
    } finally {
      setCopyLoading(prev => ({ ...prev, [key]: false }));
    }
  };

  // Handler for copying list view markdown
  const handleCopyListViewMarkdown = async (singleMonth?: string) => {
    if (!aggregatedAnalysis) return;

    const key = singleMonth ? `list-view-${singleMonth}` : 'list-view';
    setCopyLoading(prev => ({ ...prev, [key]: true }));
    setCopySuccess(prev => ({ ...prev, [key]: false }));

    try {
      const markdown = generateListViewMarkdown(
        selectedMonths,
        userAnalyses,
        aggregatedAnalysis,
        singleMonth
      );
      const success = await copyToClipboard(markdown);

      if (success) {
        setCopySuccess(prev => ({ ...prev, [key]: true }));
        setTimeout(() => {
          setCopySuccess(prev => ({ ...prev, [key]: false }));
        }, 2000);
      }
    } catch (err) {
      console.error('Failed to generate list view markdown:', err);
    } finally {
      setCopyLoading(prev => ({ ...prev, [key]: false }));
    }
  };

  // Handler for copying product table markdown
  const handleCopyProductTableMarkdown = async (
    products: Array<{
      brand: string;
      model: string;
      count: number;
      comment_ids: string[];
      handle_brand?: string;
      knot_brand?: string;
      knot_model?: string;
    }>,
    productType: string
  ) => {
    if (!aggregatedAnalysis) return;

    const key = `product-${productType}`;
    setCopyLoading(prev => ({ ...prev, [key]: true }));
    setCopySuccess(prev => ({ ...prev, [key]: false }));

    try {
      const markdown = await generateProductTableMarkdown(
        products,
        productType,
        aggregatedAnalysis,
        selectedMonths
      );
      const success = await copyToClipboard(markdown);

      if (success) {
        setCopySuccess(prev => ({ ...prev, [key]: true }));
        setTimeout(() => {
          setCopySuccess(prev => ({ ...prev, [key]: false }));
        }, 2000);
      }
    } catch (err) {
      console.error(`Failed to generate ${productType} table markdown:`, err);
    } finally {
      setCopyLoading(prev => ({ ...prev, [key]: false }));
    }
  };

  const handleMonthChange = (months: string[]) => {
    setSelectedMonths(months);
    setSelectedUser('');
    setAggregatedAnalysis(null);
    setUserAnalyses([]);
    if (months.length > 0) {
      fetchUsersForMonths(months);
    }
  };

  const handleUserSelect = (username: string) => {
    try {
      setSelectedUser(username);
      setAggregatedAnalysis(null);
      setUserAnalyses([]);
      if (selectedMonths.length > 0 && username) {
        fetchUserAnalyses(selectedMonths, username);
      }
    } catch (error) {
      console.error('[MonthlyUserPosts] Error in handleUserSelect', error);
    }
  };

  const handleUserSearch = (searchTerm: string) => {
    if (searchTerm.trim() === '') {
      if (selectedMonths.length > 0) {
        fetchUsersForMonths(selectedMonths);
      }
    } else {
      // Filter users locally for better performance
      const filteredUsers = users.filter(user =>
        user.username.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setUsers(filteredUsers);
    }
  };

  const renderCalendarView = () => {    if (!aggregatedAnalysis || selectedMonths.length === 0) {
      return (
        <div className='flex items-center justify-center h-64 text-muted-foreground'>
          Select a user to see their posting pattern
        </div>
      );
    }

    return (
      <div className='space-y-8'>
        {/* Aggregated summary when multiple months */}
        {selectedMonths.length > 1 && aggregatedAnalysis && (
          <div className='text-center mb-4'>
            <h3 className='text-lg font-semibold'>{selectedMonths.length} months selected</h3>
            <p className='text-sm text-muted-foreground'>
              Posted: {aggregatedAnalysis.posted_days} days, Missed: {aggregatedAnalysis.missed_days}{' '}
              days
            </p>
          </div>
        )}

        {/* Separate calendar section for each month */}
        {selectedMonths.map(month => {
          const monthData = userAnalyses.find(a => a.month === month);
          const monthAnalysis = monthData?.analysis || null;          if (!monthAnalysis) return null;

          // Parse the month to get year and month number
          const [year, monthNum] = month.split('-').map(Number);          const startDate = new Date(year, monthNum - 1, 1);
          const endDate = new Date(year, monthNum, 0);
          const daysInMonth = endDate.getDate();

          // Create array of dates for the month
          const dates = Array.from({ length: daysInMonth }, (_, i) => i + 1);

          // Convert posted dates to day numbers for easy lookup
          const postedDays = new Set(
            monthAnalysis.posted_dates.map(dateStr => {
              const date = new Date(dateStr + 'T00:00:00'); // Add time to avoid timezone issues
              return date.getDate();
            })
          );

          return (
            <div key={month} className='space-y-4'>
              <div className='text-center relative'>
                <div className='absolute top-0 right-0'>
                  <Button
                    variant='outline'
                    size='sm'
                    onClick={() => handleCopyCalendarMarkdown(month)}
                    disabled={copyLoading[`calendar-${month}`]}
                    className='flex items-center gap-2'
                  >
                    {copyLoading[`calendar-${month}`] ? (
                      <Loader2 className='h-4 w-4 animate-spin' />
                    ) : copySuccess[`calendar-${month}`] ? (
                      <Check className='h-4 w-4' />
                    ) : (
                      <Copy className='h-4 w-4' />
                    )}
                    {copySuccess[`calendar-${month}`] ? 'Copied!' : 'Copy to markdown'}
                  </Button>
                </div>
                <h3 className='text-lg font-semibold'>
                  {new Date(year, monthNum - 1).toLocaleDateString('en-US', {
                    month: 'long',
                    year: 'numeric',
                  })}
                </h3>
                <p className='text-sm text-muted-foreground'>
                  Posted: {monthAnalysis.posted_days} days, Missed: {monthAnalysis.missed_days} days
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
                  const isPosted = postedDays.has(day);
                  const dateStr = `${year}-${String(monthNum).padStart(2, '0')}-${String(day).padStart(2, '0')}`;                  const dayCommentIds = monthAnalysis.comments_by_date[dateStr] || [];                  return (
                    <div
                      key={day}
                      className={`p-2 text-center border rounded-md min-h-[60px] flex flex-col items-center justify-center ${
                        isPosted
                          ? 'bg-green-100 border-green-300 text-green-800'
                          : 'bg-red-100 border-red-300 text-red-800'
                      }`}
                    >
                      <span className='text-sm font-medium'>{day}</span>
                      {isPosted && dayCommentIds.length > 0 && (
                        <div className='mt-1'>
                          {(() => {
                            try {
                              return (
                                <CommentDisplay
                                  commentIds={dayCommentIds}
                                  onCommentClick={commentId => handleCommentClick(commentId, dayCommentIds)}
                                />
                              );
                            } catch (error) {                              return <span className='text-xs text-red-500'>Error</span>;
                            }
                          })()}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  const renderListView = () => {    if (!aggregatedAnalysis || selectedMonths.length === 0) {
      return (
        <div className='flex items-center justify-center h-64 text-muted-foreground'>
          Select a user to see their posting pattern
        </div>
      );
    }

    return (
      <div className='space-y-8'>
        {/* Aggregated summary when multiple months */}
        {selectedMonths.length > 1 && aggregatedAnalysis && (
          <div className='text-center mb-4 relative'>
            <div className='absolute top-0 right-0'>
              <Button
                variant='outline'
                size='sm'
                onClick={handleCopyListViewMarkdown}
                disabled={copyLoading['list-view']}
                className='flex items-center gap-2'
              >
                {copyLoading['list-view'] ? (
                  <Loader2 className='h-4 w-4 animate-spin' />
                ) : copySuccess['list-view'] ? (
                  <Check className='h-4 w-4' />
                ) : (
                  <Copy className='h-4 w-4' />
                )}
                {copySuccess['list-view'] ? 'Copied!' : 'Copy to markdown'}
              </Button>
            </div>
            <h3 className='text-lg font-semibold'>{selectedMonths.length} months selected</h3>
            <p className='text-sm text-muted-foreground'>
              Posted: {aggregatedAnalysis.posted_days} days, Missed: {aggregatedAnalysis.missed_days}{' '}
              days
            </p>
          </div>
        )}

        {/* Copy button for single month list view */}
        {selectedMonths.length === 1 && (
          <div className='flex justify-end mb-4'>
            <Button
              variant='outline'
              size='sm'
              onClick={handleCopyListViewMarkdown}
              disabled={copyLoading['list-view']}
              className='flex items-center gap-2'
            >
              {copyLoading['list-view'] ? (
                <Loader2 className='h-4 w-4 animate-spin' />
              ) : copySuccess['list-view'] ? (
                <Check className='h-4 w-4' />
              ) : (
                <Copy className='h-4 w-4' />
              )}
              {copySuccess['list-view'] ? 'Copied!' : 'Copy to markdown'}
            </Button>
          </div>
        )}

        {/* Separate section for each month */}
        {selectedMonths.map(month => {
          const monthData = userAnalyses.find(a => a.month === month);
          const monthAnalysis = monthData?.analysis || null;

          if (!monthAnalysis) return null;

          const [year, monthNum] = month.split('-').map(Number);
          const daysInMonth = new Date(year, monthNum, 0).getDate();
          const postedDays = new Set(
            monthAnalysis.posted_dates.map(dateStr => {
              const date = new Date(dateStr + 'T00:00:00'); // Add time to avoid timezone issues
              return date.getDate();
            })
          );

          return (
            <div key={month} className='space-y-4'>
              <div className='text-center mb-4 relative'>
                <div className='absolute top-0 right-0'>
                  <Button
                    variant='outline'
                    size='sm'
                    onClick={() => handleCopyListViewMarkdown(month)}
                    disabled={copyLoading[`list-view-${month}`] || copyLoading['list-view']}
                    className='flex items-center gap-2'
                  >
                    {copyLoading[`list-view-${month}`] || copyLoading['list-view'] ? (
                      <Loader2 className='h-4 w-4 animate-spin' />
                    ) : copySuccess[`list-view-${month}`] || copySuccess['list-view'] ? (
                      <Check className='h-4 w-4' />
                    ) : (
                      <Copy className='h-4 w-4' />
                    )}
                    {copySuccess[`list-view-${month}`] || copySuccess['list-view']
                      ? 'Copied!'
                      : 'Copy to markdown'}
                  </Button>
                </div>
                <h3 className='text-lg font-semibold'>
                  {new Date(year, monthNum - 1).toLocaleDateString('en-US', {
                    month: 'long',
                    year: 'numeric',
                  })}
                </h3>
                <p className='text-sm text-muted-foreground'>
                  Posted: {monthAnalysis.posted_days} days, Missed: {monthAnalysis.missed_days} days
                </p>
              </div>

              <div className='space-y-2'>
                {Array.from({ length: daysInMonth }, (_, i) => {
                  const day = i + 1;
                  const isPosted = postedDays.has(day);
                  const dateStr = `${year}-${String(monthNum).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
                  const dayCommentIds = monthAnalysis.comments_by_date[dateStr] || [];

                  return (
                    <div
                      key={day}
                      className={`flex items-center justify-between p-3 border rounded-lg ${
                        isPosted ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
                      }`}
                    >
                      <div className='flex items-center space-x-3'>
                        <span className='font-medium'>Day {day}</span>
                        <Badge
                          variant={isPosted ? 'default' : 'destructive'}
                          className={isPosted ? 'bg-green-600' : ''}
                        >
                          {isPosted ? 'Posted' : 'Missed'}
                        </Badge>
                      </div>
                      {isPosted && dayCommentIds.length > 0 && (
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
        })}
      </div>
    );
  };

  try {
    return (
    <div className='container mx-auto p-6 space-y-6'>
      <div className='flex items-center justify-between'>
        <div>
          <h1 className='text-3xl font-bold'>Monthly User Posts</h1>
          <p className='text-muted-foreground'>Analyze user posting patterns for any month</p>
        </div>
      </div>

      {/* Month and User Selection */}
      <Card>
        <CardHeader>
          <CardTitle>Select Month and User</CardTitle>
        </CardHeader>
        <CardContent className='space-y-4'>
          {/* Month Selection */}
          <div className='space-y-2'>
            <Label htmlFor='month'>Month</Label>
            <MonthSelector
              selectedMonths={selectedMonths}
              onMonthsChange={handleMonthChange}
              multiple={true}
              label=''
            />
          </div>

          {/* User Selection */}
          {selectedMonths.length > 0 && (
            <div className='space-y-2'>
              <Label htmlFor='user'>User</Label>
              <div className='flex space-x-2'>
                <Input
                  id='user'
                  placeholder='Search for a user...'
                  value={selectedUser}
                  onChange={e => setSelectedUser(e.target.value)}
                  onKeyUp={e => handleUserSearch(e.currentTarget.value)}
                  className='flex-1'
                />
                <Button
                  onClick={() => handleUserSelect(selectedUser)}
                  disabled={!selectedUser.trim()}
                >
                  Analyze
                </Button>
              </div>

              {/* User Suggestions */}
              {users.length > 0 && (
                <div className='mt-2 space-y-1'>
                  {users.slice(0, 10).map(user => (
                    <div
                      key={user.username}
                      className='flex items-center justify-between p-2 hover:bg-muted rounded cursor-pointer'
                      onClick={() => handleUserSelect(user.username)}
                    >
                      <span>{user.username}</span>
                      <Badge variant='outline'>{user.post_count} posts</Badge>
                    </div>
                  ))}
                  {users.length > 10 && (
                    <div className='text-sm text-muted-foreground text-center'>
                      +{users.length - 10} more users
                    </div>
                  )}
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
            <div className='mt-2 text-sm text-muted-foreground text-center'>
              Please check that the selected months have data available and try again.
            </div>
          </CardContent>
        </Card>
      )}

      {/* Analysis Results */}
      {aggregatedAnalysis && (
        <Card>
          <CardHeader>
            <div className='flex items-center justify-between'>
              <CardTitle>
                Analysis for {aggregatedAnalysis.user} -{' '}
                {selectedMonths.length === 1
                  ? selectedMonths[0]
                  : `${selectedMonths.length} months`}
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
                  variant={viewMode === 'list' ? 'default' : 'outline'}
                  size='sm'
                  onClick={() => setViewMode('list')}
                >
                  <ListIcon className='h-4 w-4 mr-2' />
                  List
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
                {(() => {
                  try {
                    return viewMode === 'calendar' ? renderCalendarView() : renderListView();
                  } catch (error) {                    return <div className='text-red-500'>Error rendering view: {error instanceof Error ? error.message : String(error)}</div>;
                  }
                })()}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Product Usage Tables */}
      {aggregatedAnalysis && (
        <div className='space-y-6'>
          {/* Razors Table */}
          {aggregatedAnalysis && aggregatedAnalysis.razors.length > 0 && (
            <Card>
              <CardHeader>
                <div className='flex items-center justify-between'>
                  <CardTitle>Razors Used</CardTitle>
                  <Button
                    variant='outline'
                    size='sm'
                    onClick={() => handleCopyProductTableMarkdown(aggregatedAnalysis.razors, 'razor')}
                    disabled={copyLoading['product-razor']}
                    className='flex items-center gap-2'
                  >
                    {copyLoading['product-razor'] ? (
                      <Loader2 className='h-4 w-4 animate-spin' />
                    ) : copySuccess['product-razor'] ? (
                      <Check className='h-4 w-4' />
                    ) : (
                      <Copy className='h-4 w-4' />
                    )}
                    {copySuccess['product-razor'] ? 'Copied!' : 'Copy to markdown'}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className='overflow-x-auto'>
                  <table className='w-full border-collapse border border-border'>
                    <thead>
                      <tr className='bg-muted'>
                        <th className='border border-border p-2 text-center'>#</th>
                        <th className='border border-border p-2 text-left'>Brand</th>
                        <th className='border border-border p-2 text-left'>Model</th>
                        <th className='border border-border p-2 text-center'>Count</th>
                        <th className='border border-border p-2 text-left'>Usage Dates</th>
                        <th className='border border-border p-2 text-left'>Comment IDs</th>
                      </tr>
                    </thead>
                    <tbody>
                      {aggregatedAnalysis.razors.map((razor, index) => (
                        <tr key={razor.key} className='hover:bg-muted/50'>
                          <td className='border border-border p-2 text-center font-medium'>
                            {index + 1}
                          </td>
                          <td className='border border-border p-2'>{razor.brand}</td>
                          <td className='border border-border p-2'>{razor.model}</td>
                          <td className='border border-border p-2 text-center'>{razor.count}</td>
                          <td className='border border-border p-2'>
                            <CommentDisplay
                              commentIds={razor.comment_ids}
                              onCommentClick={commentId =>
                                handleCommentClick(commentId, razor.comment_ids)
                              }
                              displayMode='dates'
                              dates={getProductUsageDates(razor.comment_ids)}
                              expanded={expandedProducts[getProductKey('razor', razor)]}
                              onExpandChange={expanded =>
                                handleProductExpandChange(getProductKey('razor', razor), expanded)
                              }
                            />
                          </td>
                          <td className='border border-border p-2'>
                            <CommentDisplay
                              commentIds={razor.comment_ids}
                              onCommentClick={commentId =>
                                handleCommentClick(commentId, razor.comment_ids)
                              }
                              expanded={expandedProducts[getProductKey('razor', razor)]}
                              onExpandChange={expanded =>
                                handleProductExpandChange(getProductKey('razor', razor), expanded)
                              }
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Blades Table */}
          {aggregatedAnalysis && aggregatedAnalysis.blades.length > 0 && (
            <Card>
              <CardHeader>
                <div className='flex items-center justify-between'>
                  <CardTitle>Blades Used</CardTitle>
                  <Button
                    variant='outline'
                    size='sm'
                    onClick={() => handleCopyProductTableMarkdown(aggregatedAnalysis.blades, 'blade')}
                    disabled={copyLoading['product-blade']}
                    className='flex items-center gap-2'
                  >
                    {copyLoading['product-blade'] ? (
                      <Loader2 className='h-4 w-4 animate-spin' />
                    ) : copySuccess['product-blade'] ? (
                      <Check className='h-4 w-4' />
                    ) : (
                      <Copy className='h-4 w-4' />
                    )}
                    {copySuccess['product-blade'] ? 'Copied!' : 'Copy to markdown'}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className='overflow-x-auto'>
                  <table className='w-full border-collapse border border-border'>
                    <thead>
                      <tr className='bg-muted'>
                        <th className='border border-border p-2 text-center'>#</th>
                        <th className='border border-border p-2 text-left'>Brand</th>
                        <th className='border border-border p-2 text-left'>Model</th>
                        <th className='border border-border p-2 text-center'>Count</th>
                        <th className='border border-border p-2 text-left'>Usage Dates</th>
                        <th className='border border-border p-2 text-left'>Comment IDs</th>
                      </tr>
                    </thead>
                    <tbody>
                      {aggregatedAnalysis.blades.map((blade, index) => (
                        <tr key={blade.key} className='hover:bg-muted/50'>
                          <td className='border border-border p-2 text-center font-medium'>
                            {index + 1}
                          </td>
                          <td className='border border-border p-2'>{blade.brand}</td>
                          <td className='border border-border p-2'>{blade.model}</td>
                          <td className='border border-border p-2 text-center'>{blade.count}</td>
                          <td className='border border-border p-2'>
                            <CommentDisplay
                              commentIds={blade.comment_ids}
                              onCommentClick={commentId =>
                                handleCommentClick(commentId, blade.comment_ids)
                              }
                              displayMode='dates'
                              dates={getProductUsageDates(blade.comment_ids)}
                              expanded={expandedProducts[getProductKey('blade', blade)]}
                              onExpandChange={expanded =>
                                handleProductExpandChange(getProductKey('blade', blade), expanded)
                              }
                            />
                          </td>
                          <td className='border border-border p-2'>
                            <CommentDisplay
                              commentIds={blade.comment_ids}
                              onCommentClick={commentId =>
                                handleCommentClick(commentId, blade.comment_ids)
                              }
                              expanded={expandedProducts[getProductKey('blade', blade)]}
                              onExpandChange={expanded =>
                                handleProductExpandChange(getProductKey('blade', blade), expanded)
                              }
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Brushes Table */}
          {aggregatedAnalysis && aggregatedAnalysis.brushes.length > 0 && (
            <Card>
              <CardHeader>
                <div className='flex items-center justify-between'>
                  <CardTitle>Brushes Used</CardTitle>
                  <Button
                    variant='outline'
                    size='sm'
                    onClick={() => handleCopyProductTableMarkdown(aggregatedAnalysis.brushes, 'brush')}
                    disabled={copyLoading['product-brush']}
                    className='flex items-center gap-2'
                  >
                    {copyLoading['product-brush'] ? (
                      <Loader2 className='h-4 w-4 animate-spin' />
                    ) : copySuccess['product-brush'] ? (
                      <Check className='h-4 w-4' />
                    ) : (
                      <Copy className='h-4 w-4' />
                    )}
                    {copySuccess['product-brush'] ? 'Copied!' : 'Copy to markdown'}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className='overflow-x-auto'>
                  <table className='w-full border-collapse border border-border'>
                    <thead>
                      <tr className='bg-muted'>
                        <th className='border border-border p-2 text-center'>#</th>
                        <th className='border border-border p-2 text-left'>Brand</th>
                        <th className='border border-border p-2 text-left'>Model</th>
                        <th className='border border-border p-2 text-left'>Handle Brand</th>
                        <th className='border border-border p-2 text-left'>Knot Brand</th>
                        <th className='border border-border p-2 text-left'>Knot Model</th>
                        <th className='border border-border p-2 text-center'>Count</th>
                        <th className='border border-border p-2 text-left'>Usage Dates</th>
                        <th className='border border-border p-2 text-left'>Comment IDs</th>
                      </tr>
                    </thead>
                    <tbody>
                      {aggregatedAnalysis.brushes.map((brush, index) => (
                        <tr key={brush.key} className='hover:bg-muted/50'>
                          <td className='border border-border p-2 text-center font-medium'>
                            {index + 1}
                          </td>
                          <td className='border border-border p-2'>{brush.brand || '-'}</td>
                          <td className='border border-border p-2'>{brush.model || '-'}</td>
                          <td className='border border-border p-2'>{brush.handle_brand || '-'}</td>
                          <td className='border border-border p-2'>{brush.knot_brand || '-'}</td>
                          <td className='border border-border p-2'>{brush.knot_model || '-'}</td>
                          <td className='border border-border p-2 text-center'>{brush.count}</td>
                          <td className='border border-border p-2'>
                            <CommentDisplay
                              commentIds={brush.comment_ids}
                              onCommentClick={commentId =>
                                handleCommentClick(commentId, brush.comment_ids)
                              }
                              displayMode='dates'
                              dates={getProductUsageDates(brush.comment_ids)}
                              expanded={expandedProducts[getProductKey('brush', brush)]}
                              onExpandChange={expanded =>
                                handleProductExpandChange(getProductKey('brush', brush), expanded)
                              }
                            />
                          </td>
                          <td className='border border-border p-2'>
                            <CommentDisplay
                              commentIds={brush.comment_ids}
                              onCommentClick={commentId =>
                                handleCommentClick(commentId, brush.comment_ids)
                              }
                              expanded={expandedProducts[getProductKey('brush', brush)]}
                              onExpandChange={expanded =>
                                handleProductExpandChange(getProductKey('brush', brush), expanded)
                              }
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Soaps Table */}
          {aggregatedAnalysis && aggregatedAnalysis.soaps.length > 0 && (
            <Card>
              <CardHeader>
                <div className='flex items-center justify-between'>
                  <CardTitle>Soaps Used</CardTitle>
                  <Button
                    variant='outline'
                    size='sm'
                    onClick={() => handleCopyProductTableMarkdown(aggregatedAnalysis.soaps, 'soap')}
                    disabled={copyLoading['product-soap']}
                    className='flex items-center gap-2'
                  >
                    {copyLoading['product-soap'] ? (
                      <Loader2 className='h-4 w-4 animate-spin' />
                    ) : copySuccess['product-soap'] ? (
                      <Check className='h-4 w-4' />
                    ) : (
                      <Copy className='h-4 w-4' />
                    )}
                    {copySuccess['product-soap'] ? 'Copied!' : 'Copy to markdown'}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className='overflow-x-auto'>
                  <table className='w-full border-collapse border border-border'>
                    <thead>
                      <tr className='bg-muted'>
                        <th className='border border-border p-2 text-center'>#</th>
                        <th className='border border-border p-2 text-left'>Brand</th>
                        <th className='border border-border p-2 text-left'>Scent</th>
                        <th className='border border-border p-2 text-center'>Count</th>
                        <th className='border border-border p-2 text-left'>Usage Dates</th>
                        <th className='border border-border p-2 text-left'>Comment IDs</th>
                      </tr>
                    </thead>
                    <tbody>
                      {aggregatedAnalysis.soaps.map((soap, index) => (
                        <tr key={soap.key} className='hover:bg-muted/50'>
                          <td className='border border-border p-2 text-center font-medium'>
                            {index + 1}
                          </td>
                          <td className='border border-border p-2'>{soap.brand}</td>
                          <td className='border border-border p-2'>{soap.model}</td>
                          <td className='border border-border p-2 text-center'>{soap.count}</td>
                          <td className='border border-border p-2'>
                            <CommentDisplay
                              commentIds={soap.comment_ids}
                              onCommentClick={commentId =>
                                handleCommentClick(commentId, soap.comment_ids)
                              }
                              displayMode='dates'
                              dates={getProductUsageDates(soap.comment_ids)}
                              expanded={expandedProducts[getProductKey('soap', soap)]}
                              onExpandChange={expanded =>
                                handleProductExpandChange(getProductKey('soap', soap), expanded)
                              }
                            />
                          </td>
                          <td className='border border-border p-2'>
                            <CommentDisplay
                              commentIds={soap.comment_ids}
                              onCommentClick={commentId =>
                                handleCommentClick(commentId, soap.comment_ids)
                              }
                              expanded={expandedProducts[getProductKey('soap', soap)]}
                              onExpandChange={expanded =>
                                handleProductExpandChange(getProductKey('soap', soap), expanded)
                              }
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}

          {/* No Products Message */}
          {aggregatedAnalysis &&
            aggregatedAnalysis.razors.length === 0 &&
            aggregatedAnalysis.blades.length === 0 &&
            aggregatedAnalysis.brushes.length === 0 &&
            aggregatedAnalysis.soaps.length === 0 && (
              <Card>
                <CardContent className='pt-6'>
                  <div className='text-center text-muted-foreground'>
                    No product data available for this user in this month.
                  </div>
                </CardContent>
              </Card>
            )}
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
  } catch (error) {
    console.error('[MonthlyUserPosts] ====== ERROR DURING RENDER ======', error);
    console.error('[MonthlyUserPosts] Error details:', error instanceof Error ? error.stack : String(error));
    return (
      <div className='container mx-auto p-6'>
        <div className='text-red-500'>
          <h1>Error rendering MonthlyUserPosts</h1>
          <p>{error instanceof Error ? error.message : String(error)}</p>
          <pre>{error instanceof Error ? error.stack : String(error)}</pre>
        </div>
      </div>
    );
  }
};

export default MonthlyUserPosts;
