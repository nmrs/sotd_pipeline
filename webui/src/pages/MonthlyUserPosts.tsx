import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Calendar as CalendarIcon, List as ListIcon, Loader2 } from 'lucide-react';
import { CommentDisplay } from '@/components/domain/CommentDisplay';
import axios from 'axios';

interface MonthData {
    month: string;
    has_data: boolean;
    user_count: number;
}

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
}

const MonthlyUserPosts: React.FC = () => {
    const [selectedMonth, setSelectedMonth] = useState<string>('');
    const [selectedUser, setSelectedUser] = useState<string>('');
    const [availableMonths, setAvailableMonths] = useState<MonthData[]>([]);
    const [users, setUsers] = useState<UserData[]>([]);
    const [userAnalysis, setUserAnalysis] = useState<UserPostingAnalysis | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string>('');
    const [viewMode, setViewMode] = useState<'calendar' | 'list'>('calendar');

    // Fetch available months on component mount
    useEffect(() => {
        fetchAvailableMonths();
    }, []);

    const fetchAvailableMonths = async () => {
        try {
            const response = await axios.get('/api/monthly-user-posts/months');
            setAvailableMonths(response.data);
            // Set first available month as default
            if (response.data.length > 0) {
                setSelectedMonth(response.data[0].month);
            }
        } catch (err) {
            setError('Failed to fetch available months');
            console.error(err);
        }
    };

    const fetchUsersForMonth = async (month: string) => {
        try {
            setLoading(true);
            const response = await axios.get(`/api/monthly-user-posts/users/${month}`);
            setUsers(response.data);
        } catch (err) {
            setError('Failed to fetch users for month');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const fetchUserAnalysis = async (month: string, username: string) => {
        try {
            setLoading(true);
            const response = await axios.get(`/api/monthly-user-posts/analysis/${month}/${username}`);
            setUserAnalysis(response.data);
        } catch (err) {
            setError('Failed to fetch user analysis');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleMonthChange = (month: string) => {
        setSelectedMonth(month);
        setSelectedUser('');
        setUserAnalysis(null);
        if (month) {
            fetchUsersForMonth(month);
        }
    };

    const handleUserSelect = (username: string) => {
        setSelectedUser(username);
        if (selectedMonth && username) {
            fetchUserAnalysis(selectedMonth, username);
        }
    };

    const handleUserSearch = (searchTerm: string) => {
        if (searchTerm.trim() === '') {
            fetchUsersForMonth(selectedMonth);
        } else {
            // Filter users locally for better performance
            const filteredUsers = users.filter(user =>
                user.username.toLowerCase().includes(searchTerm.toLowerCase())
            );
            setUsers(filteredUsers);
        }
    };

    const renderCalendarView = () => {
        if (!userAnalysis) {
            return (
                <div className="flex items-center justify-center h-64 text-muted-foreground">
                    Select a user to see their posting pattern
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

                // Convert posted dates to day numbers for easy lookup
        const postedDays = new Set(
            userAnalysis.posted_dates.map(dateStr => {
                const date = new Date(dateStr + 'T00:00:00');  // Add time to avoid timezone issues
                return date.getDate();
            })
        );

        return (
            <div className="space-y-4">
                <div className="text-center">
                    <h3 className="text-lg font-semibold">
                        {new Date(year, month - 1).toLocaleDateString('en-US', {
                            month: 'long',
                            year: 'numeric'
                        })}
                    </h3>
                    <p className="text-sm text-muted-foreground">
                        Posted: {userAnalysis.posted_days} days, Missed: {userAnalysis.missed_days} days
                    </p>
                </div>

                <div className="grid grid-cols-7 gap-1">
                    {/* Day headers */}
                    {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
                        <div key={day} className="p-2 text-center text-sm font-medium text-muted-foreground">
                            {day}
                        </div>
                    ))}

                    {/* Empty cells for days before month starts */}
                    {Array.from({ length: startDate.getDay() }, (_, i) => (
                        <div key={`empty-${i}`} className="p-2" />
                    ))}

                    {/* Month days */}
                    {dates.map(day => {
                        const isPosted = postedDays.has(day);
                        const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
                        const dayCommentIds = userAnalysis.comments_by_date[dateStr] || [];
                        
                        return (
                            <div
                                key={day}
                                className={`p-2 text-center border rounded-md min-h-[60px] flex flex-col items-center justify-center ${isPosted
                                    ? 'bg-green-100 border-green-300 text-green-800'
                                    : 'bg-red-100 border-red-300 text-red-800'
                                    }`}
                            >
                                <span className="text-sm font-medium">{day}</span>
                                {isPosted && dayCommentIds.length > 0 && (
                                    <div className="mt-1">
                                        <CommentDisplay
                                            commentIds={dayCommentIds}
                                            onCommentClick={(commentId) => console.log('Comment clicked:', commentId)}
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

    const renderListView = () => {
        if (!userAnalysis) {
            return (
                <div className="flex items-center justify-center h-64 text-muted-foreground">
                    Select a user to see their posting pattern
                </div>
            );
        }

        const [year, month] = selectedMonth.split('-').map(Number);
        const daysInMonth = new Date(year, month, 0).getDate();
        const postedDays = new Set(
            userAnalysis.posted_dates.map(dateStr => {
                const date = new Date(dateStr + 'T00:00:00');  // Add time to avoid timezone issues
                return date.getDate();
            })
        );

        return (
            <div className="space-y-4">
                <div className="text-center mb-4">
                    <h3 className="text-lg font-semibold">
                        {new Date(year, month - 1).toLocaleDateString('en-US', {
                            month: 'long',
                            year: 'numeric'
                        })}
                    </h3>
                    <p className="text-sm text-muted-foreground">
                        Posted: {userAnalysis.posted_days} days, Missed: {userAnalysis.missed_days} days
                    </p>
                </div>

                <div className="space-y-2">
                    {Array.from({ length: daysInMonth }, (_, i) => {
                        const day = i + 1;
                        const isPosted = postedDays.has(day);
                        const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
                        const dayCommentIds = userAnalysis.comments_by_date[dateStr] || [];
                        
                        return (
                            <div
                                key={day}
                                className={`flex items-center justify-between p-3 border rounded-lg ${isPosted
                                    ? 'bg-green-50 border-green-200'
                                    : 'bg-red-50 border-red-200'
                                    }`}
                            >
                                <div className="flex items-center space-x-3">
                                    <span className="font-medium">Day {day}</span>
                                    <Badge
                                        variant={isPosted ? 'default' : 'destructive'}
                                        className={isPosted ? 'bg-green-600' : ''}
                                    >
                                        {isPosted ? 'Posted' : 'Missed'}
                                    </Badge>
                                </div>
                                {isPosted && dayCommentIds.length > 0 && (
                                    <div className="text-sm text-muted-foreground">
                                        <CommentDisplay
                                            commentIds={dayCommentIds}
                                            onCommentClick={(commentId) => console.log('Comment clicked:', commentId)}
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

    return (
        <div className="container mx-auto p-6 space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold">Monthly User Posts</h1>
                    <p className="text-muted-foreground">
                        Analyze user posting patterns for any month
                    </p>
                </div>
            </div>

            {/* Month and User Selection */}
            <Card>
                <CardHeader>
                    <CardTitle>Select Month and User</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    {/* Month Selection */}
                    <div className="space-y-2">
                        <Label htmlFor="month">Month</Label>
                        <select
                            id="month"
                            value={selectedMonth}
                            onChange={(e) => handleMonthChange(e.target.value)}
                            className="w-full p-2 border border-input rounded-md"
                        >
                            <option value="">Select a month</option>
                            {availableMonths.map((month) => (
                                <option key={month.month} value={month.month}>
                                    {month.month} ({month.user_count} users)
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* User Selection */}
                    {selectedMonth && (
                        <div className="space-y-2">
                            <Label htmlFor="user">User</Label>
                            <div className="flex space-x-2">
                                <Input
                                    id="user"
                                    placeholder="Search for a user..."
                                    value={selectedUser}
                                    onChange={(e) => setSelectedUser(e.target.value)}
                                    onKeyUp={(e) => handleUserSearch(e.currentTarget.value)}
                                    className="flex-1"
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
                                <div className="mt-2 space-y-1">
                                    {users.slice(0, 10).map((user) => (
                                        <div
                                            key={user.username}
                                            className="flex items-center justify-between p-2 hover:bg-muted rounded cursor-pointer"
                                            onClick={() => handleUserSelect(user.username)}
                                        >
                                            <span>{user.username}</span>
                                            <Badge variant="outline">{user.post_count} posts</Badge>
                                        </div>
                                    ))}
                                    {users.length > 10 && (
                                        <div className="text-sm text-muted-foreground text-center">
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
                <Card className="border-destructive">
                    <CardContent className="pt-6">
                        <div className="text-destructive text-center">{error}</div>
                    </CardContent>
                </Card>
            )}

            {/* Analysis Results */}
            {userAnalysis && (
                <Card>
                    <CardHeader>
                        <div className="flex items-center justify-between">
                            <CardTitle>
                                Analysis for {userAnalysis.user} - {selectedMonth}
                            </CardTitle>

                            {/* View Toggle */}
                            <div className="flex items-center space-x-2">
                                <Button
                                    variant={viewMode === 'calendar' ? 'default' : 'outline'}
                                    size="sm"
                                    onClick={() => setViewMode('calendar')}
                                >
                                    <CalendarIcon className="h-4 w-4 mr-2" />
                                    Calendar
                                </Button>
                                <Button
                                    variant={viewMode === 'list' ? 'default' : 'outline'}
                                    size="sm"
                                    onClick={() => setViewMode('list')}
                                >
                                    <ListIcon className="h-4 w-4 mr-2" />
                                    List
                                </Button>
                            </div>
                        </div>
                    </CardHeader>
                    <CardContent>
                        {loading ? (
                            <div className="flex items-center justify-center h-64">
                                <Loader2 className="h-8 w-8 animate-spin" />
                            </div>
                        ) : (
                            <div>
                                {viewMode === 'calendar' ? renderCalendarView() : renderListView()}
                            </div>
                        )}
                    </CardContent>
                </Card>
            )}
        </div>
    );
};

export default MonthlyUserPosts;
