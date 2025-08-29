import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { Loader2, Search, Trophy, Target, Hash, Info } from 'lucide-react';

interface BrushMatchResult {
  strategy: string;
  score: number;
  matchType: string;
  pattern: string;
  scoreBreakdown: {
    baseScore: number;
    modifiers: number;
    modifierDetails: { name: string; weight: number; description: string }[];
  };
  matchedData: {
    brand?: string;
    model?: string;
    fiber?: string;
    size?: string;
    handle?: {
      brand?: string;
      model?: string;
      source_text?: string;
    };
    knot?: {
      brand?: string;
      model?: string;
      fiber?: string;
      knot_size_mm?: number;
      source_text?: string;
    };
  };
}

interface BrushAnalysisResponse {
  results: BrushMatchResult[];
  winner: BrushMatchResult;
  enrichedData?: any;
}

export function BrushMatchingAnalyzer() {
  const [brushString, setBrushString] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [results, setResults] = useState<BrushAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [bypassCorrectMatches, setBypassCorrectMatches] = useState(false);

  const analyzeBrush = async () => {
    if (!brushString.trim()) return;

    setIsAnalyzing(true);
    setError(null);
    setResults(null);

    try {
      const response = await fetch('/api/brush-matching/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          brushString: brushString.trim(),
          bypass_correct_matches: bypassCorrectMatches
        }),
      });

      if (!response.ok) {
        throw new Error(`Analysis failed: ${response.statusText}`);
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      analyzeBrush();
    }
  };

  const getStrategyIcon = (rank: number) => {
    switch (rank) {
      case 1:
        return <Trophy className='w-4 h-4 text-yellow-500' />;
      case 2:
        return <Target className='w-4 h-4 text-gray-400' />;
      case 3:
        return <Hash className='w-4 h-4 text-orange-500' />;
      default:
        return <Hash className='w-4 h-4 text-gray-400' />;
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className='container mx-auto p-6 max-w-6xl'>
      <Card>
        <CardHeader>
          <CardTitle className='flex items-center gap-2'>
            <Search className='w-5 h-5' />
            Brush Matching Analyzer
          </CardTitle>
        </CardHeader>
        <CardContent className='space-y-6'>
          {/* Input Section */}
          <div className='mb-6'>
            <div className='flex items-center gap-4 mb-4'>
              <input
                type='text'
                value={brushString}
                onChange={(e) => setBrushString(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder='Enter brush string to analyze...'
                className='flex-1 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
              />
              <button
                onClick={analyzeBrush}
                disabled={isAnalyzing || !brushString.trim()}
                className='px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed'
              >
                {isAnalyzing ? 'Analyzing...' : 'Analyze'}
              </button>
            </div>

            <div className='flex items-center gap-2'>
              <input
                type='checkbox'
                id='bypass-correct-matches'
                checked={bypassCorrectMatches}
                onChange={(e) => setBypassCorrectMatches(e.target.checked)}
                className='w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'
              />
              <label htmlFor='bypass-correct-matches' className='text-sm text-gray-600'>
                Bypass correct_matches.yaml to see all strategies
              </label>
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <Card className='border-red-200 bg-red-50'>
              <CardContent className='pt-6'>
                <p className='text-red-600'>{error}</p>
              </CardContent>
            </Card>
          )}

          {/* Results Display */}
          {results && (
            <div className='space-y-6'>
              {/* Winner Section */}
              <Card className='border-green-200 bg-green-50'>
                <CardHeader>
                  <CardTitle className='flex items-center gap-2 text-green-800'>
                    <Trophy className='w-5 h-5' />
                    Winner: {results.winner.strategy.toUpperCase()}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className='grid grid-cols-2 gap-4'>
                    <div>
                      <p className='text-sm text-gray-600'>Strategy</p>
                      <p className='font-semibold'>{results.winner.strategy}</p>
                    </div>
                    <div>
                      <p className='text-sm text-gray-600'>Score</p>
                      <div className='flex items-baseline gap-2'>
                        <span className={`font-bold text-2xl ${getScoreColor(results.winner.score)}`}>
                          {results.winner.score}
                        </span>
                        {results.winner.scoreBreakdown.modifiers > 0 && (
                          <span className='text-sm text-green-600 font-medium'>
                            (+{results.winner.scoreBreakdown.modifiers})
                          </span>
                        )}
                      </div>
                      <div className='text-xs text-gray-500 mt-1'>
                        {results.winner.scoreBreakdown.baseScore} base + {results.winner.scoreBreakdown.modifiers} modifiers
                      </div>
                    </div>
                    <div>
                      <p className='text-sm text-gray-600'>Match Type</p>
                      <p className='font-semibold'>{results.winner.matchType || 'None'}</p>
                    </div>
                    <div>
                      <p className='text-sm text-gray-600'>Pattern</p>
                      <p className='font-mono text-sm'>{results.winner.pattern}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* All Results */}
              <Card>
                <CardHeader>
                  <CardTitle>All Strategy Results</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className='space-y-4'>
                    {results.results.map((result, index) => (
                      <Card key={result.strategy} className='border-gray-200'>
                        <CardContent className='pt-6'>
                          <div className='flex items-center justify-between mb-4'>
                            <div className='flex items-center gap-2'>
                              {getStrategyIcon(index + 1)}
                              <Badge variant='outline' className='font-mono'>
                                #{index + 1}
                              </Badge>
                              <h3 className='font-semibold text-lg'>
                                {result.strategy.toUpperCase()}
                              </h3>
                            </div>
                            <div className='text-right'>
                              <div className='flex items-baseline gap-2 justify-end'>
                                <span className={`text-2xl font-bold ${getScoreColor(result.score)}`}>
                                  {result.score}
                                </span>
                                {result.scoreBreakdown.modifiers > 0 && (
                                  <span className='text-sm text-green-600 font-medium'>
                                    (+{result.scoreBreakdown.modifiers})
                                  </span>
                                )}
                              </div>
                              <p className='text-sm text-gray-600'>{result.matchType || 'None'}</p>
                              <p className='text-xs text-gray-500'>
                                {result.scoreBreakdown.baseScore} + {result.scoreBreakdown.modifiers}
                              </p>
                            </div>
                          </div>

                          {/* Score Breakdown */}
                          <div className='mb-4'>
                            <h4 className='font-medium mb-2'>Score Breakdown</h4>
                            <div className='grid grid-cols-3 gap-4 text-sm'>
                              <div>
                                <p className='text-gray-600'>Base Score</p>
                                <p className='font-semibold'>{result.scoreBreakdown.baseScore}</p>
                                <p className='text-xs text-gray-500'>Strategy match</p>
                              </div>
                              <div>
                                <p className='text-gray-600'>Modifiers</p>
                                <p className='font-semibold'>
                                  {result.scoreBreakdown.modifiers > 0 ? '+' : ''}
                                  {result.scoreBreakdown.modifiers}
                                </p>
                                <p className='text-xs text-gray-500'>
                                  {result.scoreBreakdown.modifiers > 0 ? 'Bonus points' : 'No bonuses'}
                                </p>
                              </div>
                              <div>
                                <p className='text-gray-600'>Total</p>
                                <p className='font-semibold'>
                                  {result.scoreBreakdown.baseScore +
                                    result.scoreBreakdown.modifiers}
                                </p>
                                <p className='text-xs text-gray-500'>Final score</p>
                              </div>
                            </div>
                          </div>

                          {/* Modifier Details */}
                          <div className='mb-4'>
                            <h4 className='font-medium mb-2'>Modifier Details</h4>
                            <div className='text-xs text-gray-600 mb-2 bg-gray-50 p-2 rounded'>
                              <p className='font-medium'>About Modifiers:</p>
                              <p>Modifiers are bonus points awarded for:</p>
                              <ul className='list-disc list-inside ml-2 mt-1 space-y-1'>
                                <li>Fiber type matches (badger, boar, synthetic)</li>
                                <li>Size specifications (knot diameter)</li>
                                <li>Handle material matches</li>
                                <li>Brand/model confidence</li>
                                <li>Pattern specificity</li>
                              </ul>
                            </div>
                            {result.scoreBreakdown.modifierDetails.length > 0 ? (
                              <div className='space-y-1'>
                                {result.scoreBreakdown.modifierDetails.map((detail, idx) => (
                                  <div key={idx} className='text-sm text-gray-700 bg-gray-50 p-2 rounded'>
                                    <div className='flex justify-between items-center'>
                                      <span className='font-medium'>{detail.name}</span>
                                      <span className='text-green-600 font-semibold'>+{detail.weight}</span>
                                    </div>
                                    <p className='text-xs text-gray-500 mt-1'>{detail.description}</p>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <div className='text-sm text-gray-500 italic'>
                                {result.scoreBreakdown.modifiers > 0 ? (
                                  <>
                                    <p>Modifiers applied: +{result.scoreBreakdown.modifiers}</p>
                                    <p className='text-xs mt-1'>
                                      (Detailed breakdown not available from backend)
                                    </p>
                                  </>
                                ) : (
                                  <p>No modifiers applied</p>
                                )}
                              </div>
                            )}
                          </div>

                          {/* Matched Data */}
                          <div>
                            <h4 className='font-medium mb-2'>Matched Data</h4>

                            <div className='space-y-2 text-sm'>
                              {/* Top Level Section - always show */}
                              <div className='border-b pb-2'>
                                <div className='text-xs text-gray-500 mb-1 font-medium'>
                                  TOP LEVEL
                                </div>
                                <div className='space-y-1'>
                                  <div className='flex justify-between'>
                                    <span className='text-gray-600'>Brand:</span>
                                    <span
                                      className={
                                        result.matchedData.brand
                                          ? 'font-semibold'
                                          : 'text-gray-400 italic'
                                      }
                                    >
                                      {result.matchedData.brand || 'Not specified'}
                                    </span>
                                  </div>
                                  <div className='flex justify-between'>
                                    <span className='text-gray-600'>Model:</span>
                                    <span
                                      className={
                                        result.matchedData.model
                                          ? 'font-semibold'
                                          : 'text-gray-400 italic'
                                      }
                                    >
                                      {result.matchedData.model || 'Not specified'}
                                    </span>
                                  </div>
                                </div>
                              </div>

                              {/* Handle Section - always show */}
                              <div className='border-b pb-2'>
                                <div className='text-xs text-gray-500 mb-1 font-medium'>HANDLE</div>
                                <div className='space-y-1'>
                                  <div className='flex justify-between'>
                                    <span className='text-gray-600'>Brand:</span>
                                    <span
                                      className={
                                        result.matchedData.handle?.brand
                                          ? 'font-semibold'
                                          : 'text-gray-400 italic'
                                      }
                                    >
                                      {result.matchedData.handle?.brand || 'Not specified'}
                                    </span>
                                  </div>
                                  <div className='flex justify-between'>
                                    <span className='text-gray-600'>Model:</span>
                                    <span
                                      className={
                                        result.matchedData.handle?.model
                                          ? 'font-semibold'
                                          : 'text-gray-400 italic'
                                      }
                                    >
                                      {result.matchedData.handle?.model || 'Not specified'}
                                    </span>
                                  </div>
                                  <div className='flex justify-between'>
                                    <span className='text-gray-600'>Source:</span>
                                    <span
                                      className={
                                        result.matchedData.handle?.source_text
                                          ? 'font-semibold text-xs'
                                          : 'text-gray-400 italic text-xs'
                                      }
                                    >
                                      {result.matchedData.handle?.source_text || 'Not specified'}
                                    </span>
                                  </div>
                                </div>
                              </div>

                              {/* Knot Section - always show */}
                              <div>
                                <div className='text-xs text-gray-500 mb-1 font-medium'>KNOT</div>
                                <div className='space-y-1'>
                                  <div className='flex justify-between'>
                                    <span className='text-gray-600'>Brand:</span>
                                    <span
                                      className={
                                        result.matchedData.knot?.brand
                                          ? 'font-semibold'
                                          : 'font-semibold'
                                      }
                                    >
                                      {result.matchedData.knot?.brand || 'Not specified'}
                                    </span>
                                  </div>
                                  <div className='flex justify-between'>
                                    <span className='text-gray-600'>Model:</span>
                                    <span
                                      className={
                                        result.matchedData.knot?.model
                                          ? 'font-semibold'
                                          : 'text-gray-400 italic'
                                      }
                                    >
                                      {result.matchedData.knot?.model || 'Not specified'}
                                    </span>
                                  </div>
                                  <div className='flex justify-between'>
                                    <span className='text-gray-600'>Fiber:</span>
                                    <span
                                      className={
                                        result.matchedData.knot?.fiber
                                          ? 'font-semibold'
                                          : 'text-gray-400 italic'
                                      }
                                    >
                                      {result.matchedData.knot?.fiber || 'Not specified'}
                                    </span>
                                  </div>
                                  <div className='flex justify-between'>
                                    <span className='text-gray-600'>Size:</span>
                                    <span
                                      className={
                                        result.matchedData.knot?.knot_size_mm
                                          ? 'font-semibold'
                                          : 'text-gray-400 italic'
                                      }
                                    >
                                      {result.matchedData.knot?.knot_size_mm
                                        ? `${result.matchedData.knot.knot_size_mm}mm`
                                        : 'Not specified'}
                                    </span>
                                  </div>
                                  <div className='flex justify-between'>
                                    <span className='text-gray-600'>Source:</span>
                                    <span
                                      className={
                                        result.matchedData.knot?.source_text
                                          ? 'font-semibold text-xs'
                                          : 'text-gray-400 italic text-xs'
                                      }
                                    >
                                      {result.matchedData.knot?.source_text || 'Not specified'}
                                    </span>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Enriched Data */}
              {results.enrichedData && (
                <Card>
                  <CardHeader>
                    <CardTitle>Enriched Data</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <pre className='bg-gray-100 p-4 rounded text-sm overflow-x-auto'>
                      {JSON.stringify(results.enrichedData, null, 2)}
                    </pre>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
