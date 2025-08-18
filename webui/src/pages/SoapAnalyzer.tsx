import React, { useState, useEffect } from 'react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Badge } from '../components/ui/badge';
import { Separator } from '../components/ui/separator';
import MonthSelector from '../components/forms/MonthSelector';

interface SoapDuplicateResult {
    text1: string;
    text2: string;
    similarity: number;
    count: number;
    maker1: string;
    scent1: string;
    maker2: string;
    scent2: string;
}

interface SoapPatternSuggestion {
    pattern: string;
    count: number;
    examples: string[];
}

interface ApiResponse {
    message: string;
    results: SoapDuplicateResult[] | SoapPatternSuggestion[];
    total_matches: number;
    months_processed: string[];
}

const SoapAnalyzer: React.FC = () => {
    const [selectedMonths, setSelectedMonths] = useState<string[]>([]);
    const [similarityThreshold, setSimilarityThreshold] = useState(0.8);
    const [limit, setLimit] = useState(10);
    const [duplicatesResult, setDuplicatesResult] = useState<ApiResponse | null>(null);
    const [patternsResult, setPatternsResult] = useState<ApiResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState('duplicates');





    const analyzeDuplicates = async () => {
        if (selectedMonths.length === 0) {
            setError('Please select at least one month');
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const monthsParam = selectedMonths.join(',');
            const url = `http://localhost:8000/soap-analyzer/duplicates?months=${monthsParam}&similarity_threshold=${similarityThreshold}&limit=${limit}`;

            const response = await fetch(url);
            if (response.ok) {
                const data = await response.json();
                setDuplicatesResult(data);
                setActiveTab('duplicates');
            } else {
                const errorData = await response.json();
                setError(errorData.detail || 'Failed to analyze duplicates');
            }
        } catch (err) {
            console.error('Error analyzing duplicates:', err);
            setError('Failed to analyze duplicates');
        } finally {
            setLoading(false);
        }
    };

    const analyzePatterns = async () => {
        if (selectedMonths.length === 0) {
            setError('Please select at least one month');
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const monthsParam = selectedMonths.join(',');
            const url = `http://localhost:8000/soap-analyzer/pattern-suggestions?months=${monthsParam}&limit=${limit}`;

            const response = await fetch(url);
            if (response.ok) {
                const data = await response.json();
                setPatternsResult(data);
                setActiveTab('patterns');
            } else {
                const errorData = await response.json();
                setError(errorData.detail || 'Failed to analyze patterns');
            }
        } catch (err) {
            console.error('Error analyzing patterns:', err);
            setError('Failed to analyze patterns');
        } finally {
            setLoading(false);
        }
    };

    const getSimilarityColor = (similarity: number) => {
        if (similarity >= 0.9) return 'bg-red-100 text-red-800';
        if (similarity >= 0.8) return 'bg-orange-100 text-orange-800';
        if (similarity >= 0.7) return 'bg-yellow-100 text-yellow-800';
        return 'bg-green-100 text-green-800';
    };

    return (
        <div className="container mx-auto p-6 space-y-6">
            <div className="text-center">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">🧼 Soap Analyzer</h1>
                <p className="text-gray-600">
                    Analyze soap matches for duplicates and pattern suggestions to improve data quality.
                </p>
            </div>

            {/* Month Selection */}
            <Card>
                <CardHeader>
                    <CardTitle>Select Months</CardTitle>
                </CardHeader>
                <CardContent>
                    <MonthSelector
                        selectedMonths={selectedMonths}
                        onMonthsChange={setSelectedMonths}
                        multiple={true}
                        label="Analysis Months"
                    />
                </CardContent>
            </Card>

            {/* Analysis Controls */}
            <Card>
                <CardHeader>
                    <CardTitle>Analysis Settings</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Similarity Threshold
                            </label>
                            <div className="flex items-center space-x-2">
                                <input
                                    type="range"
                                    min="0.5"
                                    max="1.0"
                                    step="0.1"
                                    value={similarityThreshold}
                                    onChange={(e) => setSimilarityThreshold(parseFloat(e.target.value))}
                                    className="flex-1"
                                />
                                <span className="text-sm font-mono w-12">{similarityThreshold}</span>
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Result Limit
                            </label>
                            <Input
                                type="number"
                                min="1"
                                max="100"
                                value={limit}
                                onChange={(e) => setLimit(parseInt(e.target.value) || 10)}
                                className="w-full"
                            />
                        </div>

                        <div className="flex items-end space-x-2">
                            <Button
                                onClick={analyzeDuplicates}
                                disabled={loading || selectedMonths.length === 0}
                                className="flex-1"
                            >
                                {loading ? 'Analyzing...' : 'Analyze Duplicates'}
                            </Button>
                            <Button
                                onClick={analyzePatterns}
                                disabled={loading || selectedMonths.length === 0}
                                variant="outline"
                                className="flex-1"
                            >
                                {loading ? 'Analyzing...' : 'Analyze Patterns'}
                            </Button>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Error Display */}
            {error && (
                <Alert variant="destructive">
                    <AlertDescription>{error}</AlertDescription>
                </Alert>
            )}

            {/* Results */}
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="duplicates">Duplicates Analysis</TabsTrigger>
                    <TabsTrigger value="patterns">Pattern Suggestions</TabsTrigger>
                </TabsList>

                <TabsContent value="duplicates" className="space-y-4">
                    {duplicatesResult && (
                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center justify-between">
                                    Duplicates Found
                                    <Badge variant="secondary">
                                        {duplicatesResult.results.length} results
                                    </Badge>
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="text-sm text-gray-600 mb-4">
                                    {duplicatesResult.message} • {duplicatesResult.total_matches} total matches •
                                    Months: {duplicatesResult.months_processed.join(', ')}
                                </div>

                                {duplicatesResult.results.length > 0 ? (
                                    <div className="space-y-4">
                                        {(duplicatesResult.results as SoapDuplicateResult[]).map((result, index) => (
                                            <div key={index} className="border rounded-lg p-4 space-y-2">
                                                <div className="flex items-center justify-between">
                                                    <div className="flex items-center space-x-2">
                                                        <Badge className={getSimilarityColor(result.similarity)}>
                                                            {result.similarity}
                                                        </Badge>
                                                        <span className="text-sm text-gray-500">
                                                            Count: {result.count}
                                                        </span>
                                                    </div>
                                                </div>

                                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                    <div>
                                                        <div className="font-medium text-gray-900">{result.text1}</div>
                                                        <div className="text-sm text-gray-600">
                                                            Maker: {result.maker1} • Scent: {result.scent1}
                                                        </div>
                                                    </div>
                                                    <div>
                                                        <div className="font-medium text-gray-900">{result.text2}</div>
                                                        <div className="text-sm text-gray-600">
                                                            Maker: {result.maker2} • Scent: {result.scent2}
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="text-center py-8 text-gray-500">
                                        No duplicates found with the current similarity threshold.
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    )}
                </TabsContent>

                <TabsContent value="patterns" className="space-y-4">
                    {patternsResult && (
                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center justify-between">
                                    Pattern Suggestions
                                    <Badge variant="secondary">
                                        {patternsResult.results.length} results
                                    </Badge>
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="text-sm text-gray-600 mb-4">
                                    {patternsResult.message} • {patternsResult.total_matches} total matches •
                                    Months: {patternsResult.months_processed.join(', ')}
                                </div>

                                {patternsResult.results.length > 0 ? (
                                    <div className="space-y-4">
                                        {(patternsResult.results as SoapPatternSuggestion[]).map((result, index) => (
                                            <div key={index} className="border rounded-lg p-4 space-y-3">
                                                <div className="flex items-center justify-between">
                                                    <h4 className="text-lg font-medium text-gray-900">{result.pattern}</h4>
                                                    <Badge variant="outline">{result.count} occurrences</Badge>
                                                </div>

                                                {result.examples.length > 0 && (
                                                    <div>
                                                        <div className="text-sm font-medium text-gray-700 mb-2">Examples:</div>
                                                        <div className="space-y-1">
                                                            {result.examples.map((example, idx) => (
                                                                <div key={idx} className="text-sm text-gray-600 bg-gray-50 px-3 py-2 rounded">
                                                                    {example}
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="text-center py-8 text-gray-500">
                                        No patterns found for the selected months.
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    )}
                </TabsContent>
            </Tabs>
        </div>
    );
};

export default SoapAnalyzer;
