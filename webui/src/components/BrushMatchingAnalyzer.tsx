import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { Loader2, Search, Trophy, Target, Hash, Info, Split, Component } from 'lucide-react';

interface BrushMatchResult {
  strategy: string;
  score: number;
  matchType: string;
  pattern: string;
  scoreBreakdown: {
    baseScore: number;
    modifiers: number;
    modifierDetails: { name: string; weight: number; description: string }[];
    total?: number;
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
  // Enhanced fields for detailed analysis
  componentDetails?: {
    handle?: {
      score: number;
      breakdown: Record<string, number>;
      metadata: Record<string, any>;
    };
    knot?: {
      score: number;
      breakdown: Record<string, number>;
      metadata: Record<string, any>;
    };
  };
  splitInformation?: {
    handleText: string;
    knotText: string;
    splitPriority?: string;
  };
}

interface BrushAnalysisResponse {
  results: BrushMatchResult[];
  winner: BrushMatchResult;
  enrichedData?: any;
}

// Reusable component for displaying score breakdowns
function ScoreBreakdownDisplay({
  baseScore,
  modifiers,
  modifierDetails,
  total,
}: {
  baseScore: number;
  modifiers: number;
  modifierDetails: { name: string; weight: number; description: string }[];
  total?: number;
}) {
  const finalTotal = total ?? baseScore + modifiers;

  return (
    <div className='mb-4'>
      <h4 className='font-medium mb-2'>Score Breakdown</h4>
      <div className='grid grid-cols-3 gap-4 text-sm'>
        <div>
          <p className='text-gray-600'>Base Score</p>
          <p className='font-semibold'>{baseScore}</p>
          <p className='text-xs text-gray-500'>Strategy match</p>
        </div>
        <div>
          <p className='text-gray-600'>Modifiers</p>
          <p className='font-semibold'>
            {modifiers > 0 ? '+' : ''}
            {modifiers}
          </p>
          <p className='text-xs text-gray-500'>{modifiers > 0 ? 'Bonus points' : 'No bonuses'}</p>
        </div>
        <div>
          <p className='text-gray-600'>Total</p>
          <p className='font-semibold'>{finalTotal}</p>
          <p className='text-xs text-gray-500'>Final score</p>
        </div>
      </div>
    </div>
  );
}

// Reusable component for displaying modifier details
function ModifierDetailsDisplay({
  modifierDetails,
  modifiers,
}: {
  modifierDetails: { name: string; weight: number; description: string }[];
  modifiers: number;
}) {
  return (
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
          <li>Component matching success</li>
        </ul>
      </div>
      {modifierDetails.length > 0 ? (
        <div className='space-y-1'>
          {modifierDetails.map((detail, idx) => (
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
          {modifiers > 0 ? (
            <>
              <p>Modifiers applied: +{modifiers}</p>
              <p className='text-xs mt-1'>(Detailed breakdown not available from backend)</p>
            </>
          ) : (
            <p>No modifiers applied</p>
          )}
        </div>
      )}
    </div>
  );
}

// Reusable component for displaying component details
function ComponentDetailsDisplay({
  componentDetails,
  splitInformation,
}: {
  componentDetails?: {
    handle?: { score: number; breakdown: Record<string, number>; metadata: Record<string, any> };
    knot?: { score: number; breakdown: Record<string, number>; metadata: Record<string, any> };
  };
  splitInformation?: { handleText: string; knotText: string; splitPriority?: string };
}) {
  if (!componentDetails && !splitInformation) return null;

  return (
    <div className='mb-4'>
      <h4 className='font-medium mb-2 flex items-center gap-2'>
        <Component className='w-4 h-4' />
        Component Analysis
      </h4>

      {/* Split Information */}
      {splitInformation && (
        <div className='mb-3 p-3 bg-blue-50 border border-blue-200 rounded'>
          <h5 className='font-medium text-sm text-blue-800 mb-2 flex items-center gap-2'>
            <Split className='w-4 h-4' />
            Split Information
          </h5>
          <div className='grid grid-cols-2 gap-4 text-sm'>
            <div>
              <p className='text-blue-600 font-medium'>Handle Text:</p>
              <p className='font-mono text-xs bg-white p-2 rounded border'>
                {splitInformation.handleText}
              </p>
            </div>
            <div>
              <p className='text-blue-600 font-medium'>Knot Text:</p>
              <p className='font-mono text-xs bg-white p-2 rounded border'>
                {splitInformation.knotText}
              </p>
            </div>
          </div>
          {splitInformation.splitPriority && (
            <div className='mt-2'>
              <p className='text-blue-600 font-medium'>Split Priority:</p>
              <Badge variant='outline' className='text-xs'>
                {splitInformation.splitPriority}
              </Badge>
            </div>
          )}
        </div>
      )}

      {/* Component Details */}
      {componentDetails && (
        <div className='space-y-3'>
          {/* Handle Component */}
          {componentDetails.handle && (
            <div className='p-3 bg-green-50 border border-green-200 rounded'>
              <h5 className='font-medium text-sm text-green-800 mb-2'>🖐️ Handle Component</h5>
              <div className='grid grid-cols-2 gap-4 text-sm'>
                <div>
                  <p className='text-green-600 font-medium'>Score:</p>
                  <p className='font-semibold'>{componentDetails.handle.score}</p>
                </div>
                <div>
                  <p className='text-green-600 font-medium'>Breakdown:</p>
                  <div className='space-y-1'>
                    {Object.entries(componentDetails.handle.breakdown).map(([key, value]) => (
                      <div key={key} className='flex justify-between text-xs'>
                        <span className='text-gray-600'>{key}:</span>
                        <span className='font-medium'>+{value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              {Object.keys(componentDetails.handle.metadata).length > 0 && (
                <div className='mt-2'>
                  <p className='text-green-600 font-medium text-xs'>Metadata:</p>
                  <div className='text-xs text-gray-700 bg-white p-2 rounded border mt-1'>
                    {Object.entries(componentDetails.handle.metadata).map(([key, value]) => (
                      <div key={key} className='flex justify-between'>
                        <span className='text-gray-600'>{key}:</span>
                        <span>{value || 'Not specified'}</span>
                      </div>
                    ))}
                    {/* Show pattern information inline */}
                    {componentDetails.handle.patterns?.brand_pattern && (
                      <div className='flex justify-between'>
                        <span className='text-gray-600'>pattern:</span>
                        <span className='font-mono'>{componentDetails.handle.patterns.brand_pattern}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Knot Component */}
          {componentDetails.knot && (
            <div className='p-3 bg-purple-50 border border-purple-200 rounded'>
              <h5 className='font-medium text-sm text-purple-800 mb-2'>🧶 Knot Component</h5>
              <div className='grid grid-cols-2 gap-4 text-sm'>
                <div>
                  <p className='text-purple-600 font-medium'>Score:</p>
                  <p className='font-semibold'>{componentDetails.knot.score}</p>
                </div>
                <div>
                  <p className='text-purple-600 font-medium'>Breakdown:</p>
                  <div className='space-y-1'>
                    {Object.entries(componentDetails.knot.breakdown).map(([key, value]) => (
                      <div key={key} className='flex justify-between text-xs'>
                        <span className='text-gray-600'>{key}:</span>
                        <span className='font-medium'>+{value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              {Object.keys(componentDetails.knot.metadata).length > 0 && (
                <div className='mt-2'>
                  <p className='text-purple-600 font-medium text-xs'>Metadata:</p>
                  <div className='text-xs text-gray-700 bg-white p-2 rounded border mt-1'>
                    {Object.entries(componentDetails.knot.metadata).map(([key, value]) => (
                      <div key={key} className='flex justify-between'>
                        <span className='text-gray-600'>{key}:</span>
                        <span>{value || 'Not specified'}</span>
                      </div>
                    ))}
                    {/* Show pattern information inline */}
                    {componentDetails.knot.patterns?.brand_pattern && (
                      <div className='flex justify-between'>
                        <span className='text-gray-600'>pattern:</span>
                        <span className='font-mono'>{componentDetails.knot.patterns.brand_pattern}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
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
          bypass_correct_matches: bypassCorrectMatches,
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
                onChange={e => setBrushString(e.target.value)}
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
                onChange={e => setBypassCorrectMatches(e.target.checked)}
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
                        <span
                          className={`font-bold text-2xl ${getScoreColor(results.winner.score)}`}
                        >
                          {results.winner.score}
                        </span>
                        {results.winner.scoreBreakdown.modifiers > 0 && (
                          <span className='text-sm text-green-600 font-medium'>
                            (+{results.winner.scoreBreakdown.modifiers})
                          </span>
                        )}
                      </div>
                      <div className='text-xs text-gray-500 mt-1'>
                        {results.winner.scoreBreakdown.baseScore} base +{' '}
                        {results.winner.scoreBreakdown.modifiers} modifiers
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
                    {results.results
                      .filter(result => {
                        // Filter out strategies with no valid matches
                        const hasValidData =
                          result.matchedData &&
                          (result.matchedData.brand ||
                            result.matchedData.handle ||
                            result.matchedData.knot);

                        // Also check if enrichedData has valid match information
                        const hasEnrichedData =
                          results.enrichedData &&
                          (results.enrichedData.brand ||
                            results.enrichedData.handle ||
                            results.enrichedData.knot);

                        return hasValidData || hasEnrichedData;
                      })
                      .map((result, index) => (
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
                                <Badge variant='secondary' className='bg-green-100 text-green-800'>
                                  ✓ Matched
                                </Badge>
                              </div>
                              <div className='text-right'>
                                <div className='flex items-baseline gap-2 justify-end'>
                                  <span
                                    className={`text-2xl font-bold ${getScoreColor(result.score)}`}
                                  >
                                    {result.score}
                                  </span>
                                  {result.scoreBreakdown.modifiers > 0 && (
                                    <span className='text-sm text-green-600 font-medium'>
                                      (+{result.scoreBreakdown.modifiers})
                                    </span>
                                  )}
                                </div>
                                <p className='text-sm text-gray-600'>
                                  {result.matchType || 'None'}
                                </p>
                                <p className='text-xs text-gray-500'>
                                  {result.scoreBreakdown.baseScore} +{' '}
                                  {result.scoreBreakdown.modifiers}
                                </p>
                              </div>
                            </div>

                            {/* Score Breakdown - Reusable Component */}
                            <ScoreBreakdownDisplay
                              baseScore={result.scoreBreakdown.baseScore}
                              modifiers={result.scoreBreakdown.modifiers}
                              modifierDetails={result.scoreBreakdown.modifierDetails}
                              total={result.scoreBreakdown.total}
                            />

                            {/* Modifier Details - Reusable Component */}
                            <ModifierDetailsDisplay
                              modifierDetails={result.scoreBreakdown.modifierDetails}
                              modifiers={result.scoreBreakdown.modifiers}
                            />

                            {/* Component Details - Reusable Component */}
                            <ComponentDetailsDisplay
                              componentDetails={result.componentDetails}
                              splitInformation={result.splitInformation}
                            />
                          </CardContent>
                        </Card>
                      ))}

                    {/* Non-Matching Strategies */}
                    {results.results
                      .filter(result => {
                        // Filter for strategies with no valid matches
                        const hasValidData =
                          result.matchedData &&
                          (result.matchedData.brand ||
                            result.matchedData.handle ||
                            result.matchedData.knot);

                        // Also check if enrichedData has valid match information
                        const hasEnrichedData =
                          results.enrichedData &&
                          (results.enrichedData.brand ||
                            results.enrichedData.handle ||
                            results.enrichedData.knot);

                        return !hasValidData && !hasEnrichedData;
                      })
                      .map((result, index) => (
                        <Card key={result.strategy} className='border-gray-200 bg-gray-50'>
                          <CardContent className='pt-6'>
                            <div className='flex items-center justify-between mb-4'>
                              <div className='flex items-center gap-2'>
                                <Hash className='w-4 h-4 text-gray-400' />
                                <Badge variant='outline' className='font-mono text-gray-500'>
                                  #
                                  {results.results.filter(r => {
                                    const hasValidData =
                                      r.matchedData &&
                                      (r.matchedData.brand ||
                                        r.matchedData.handle ||
                                        r.matchedData.knot);
                                    return hasValidData;
                                  }).length +
                                    index +
                                    1}
                                </Badge>
                                <h3 className='font-semibold text-lg text-gray-600'>
                                  {result.strategy.toUpperCase()}
                                </h3>
                                <Badge variant='secondary' className='bg-red-100 text-red-800'>
                                  ✗ No Match
                                </Badge>
                              </div>
                              <div className='text-right'>
                                <div className='flex items-baseline gap-2 justify-end'>
                                  <span className='text-2xl font-bold text-gray-400'>
                                    {result.score}
                                  </span>
                                  {result.scoreBreakdown.modifiers > 0 && (
                                    <span className='text-sm text-gray-500 font-medium'>
                                      (+{result.scoreBreakdown.modifiers})
                                    </span>
                                  )}
                                </div>
                                <p className='text-sm text-gray-500'>
                                  {result.matchType || 'None'}
                                </p>
                                <p className='text-xs text-gray-400'>
                                  {result.scoreBreakdown.baseScore} +{' '}
                                  {result.scoreBreakdown.modifiers}
                                </p>
                              </div>
                            </div>

                            {/* Score Breakdown for Non-Matching Strategies */}
                            <ScoreBreakdownDisplay
                              baseScore={result.scoreBreakdown.baseScore}
                              modifiers={result.scoreBreakdown.modifiers}
                              modifierDetails={result.scoreBreakdown.modifierDetails}
                              total={result.scoreBreakdown.total}
                            />

                            {/* Modifier Details for Non-Matching Strategies */}
                            <ModifierDetailsDisplay
                              modifierDetails={result.scoreBreakdown.modifierDetails}
                              modifiers={result.scoreBreakdown.modifiers}
                            />

                            {/* Component Details for Non-Matching Strategies */}
                            <ComponentDetailsDisplay
                              componentDetails={result.componentDetails}
                              splitInformation={result.splitInformation}
                            />

                            {/* No Match Explanation */}
                            <div className='mt-4 p-3 bg-red-50 border border-red-200 rounded'>
                              <h4 className='font-medium text-sm text-red-800 mb-2'>
                                Why No Match?
                              </h4>
                              <div className='text-sm text-red-700 space-y-1'>
                                <p>This strategy failed to produce a valid match because:</p>
                                <ul className='list-disc list-inside ml-4 space-y-1'>
                                  <li>No matching patterns found in the catalog</li>
                                  <li>Pattern matching failed for the input text</li>
                                  <li>
                                    Required fields (brand, model, etc.) could not be extracted
                                  </li>
                                  <li>Strategy-specific logic rejected the input</li>
                                </ul>
                                <p className='text-xs text-red-600 mt-2'>
                                  Score: {result.score} (below threshold or invalid result)
                                </p>
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
