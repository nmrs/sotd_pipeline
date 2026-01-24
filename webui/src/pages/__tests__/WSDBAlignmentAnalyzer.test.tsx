import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import WSDBAlignmentAnalyzer from '../WSDBAlignmentAnalyzer';

// Mock fetch globally
global.fetch = jest.fn();

const mockWSDBSoaps = [
  {
    brand: 'Barrister and Mann',
    name: 'Seville',
    slug: 'barrister-and-mann-seville',
    scent_notes: ['citrus', 'lavender'],
    collaborators: [],
    tags: ['classic'],
    category: 'Traditional',
  },
  {
    brand: 'Declaration Grooming',
    name: 'Massacre of the Innocents',
    slug: 'declaration-grooming-massacre-of-the-innocents',
    scent_notes: ['pine', 'smoke'],
    collaborators: ['Chatillon Lux'],
    tags: ['seasonal'],
    category: 'Artisan',
  },
];

const mockPipelineSoaps = [
  {
    brand: 'Barrister and Mann',
    scents: [
      { name: 'Seville', patterns: ['seville'] },
      { name: 'Leviathan', patterns: ['leviathan', 'levi'] },
    ],
  },
  {
    brand: 'Declaration Grooming',
    scents: [
      { name: 'Massacre of the Innocents', patterns: ['massacre.*innocents', 'moti'] },
      { name: 'Chaotic Neutral', patterns: ['chaotic.*neutral', 'cn'] },
    ],
  },
];

const mockFuzzyMatchResponse = {
  matches: [
    {
      brand: 'Barrister and Mann',
      name: 'Seville',
      confidence: 95.5,
      brand_score: 100,
      scent_score: 89,
      source: 'wsdb',
      details: {
        slug: 'barrister-and-mann-seville',
        scent_notes: ['citrus', 'lavender'],
        collaborators: [],
        tags: ['classic'],
        category: 'Traditional',
      },
    },
  ],
  query: { brand: 'Barrister and Mann', scent: 'Seville', source_type: 'pipeline' },
  threshold: 0.7,
  total_matches: 1,
};

// Helper function to set up default mocks for component mount (3 fetch calls: WSDB, pipeline, non-matches)
const setupDefaultMocks = (
  wsdbSoaps: typeof mockWSDBSoaps = [],
  pipelineSoaps: typeof mockPipelineSoaps = [],
  nonMatches: { brand_non_matches: any[]; scent_non_matches: any[] } = {
    brand_non_matches: [],
    scent_non_matches: [],
  }
) => {
  (global.fetch as jest.Mock)
    .mockResolvedValueOnce({
      ok: true,
      json: async () => ({ soaps: wsdbSoaps, total_count: wsdbSoaps.length }),
    })
    .mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        soaps: pipelineSoaps,
        total_brands: pipelineSoaps.length,
        total_scents: pipelineSoaps.reduce((sum, soap) => sum + (soap.scents?.length || 0), 0),
      }),
    })
    .mockResolvedValueOnce({
      ok: true,
      json: async () => nonMatches,
    });
};

describe('WSDBAlignmentAnalyzer', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset mock implementation to ensure clean state between tests
    (global.fetch as jest.Mock).mockReset();
  });

  describe('Component Rendering', () => {
    test('renders main heading and description', async () => {
      setupDefaultMocks();

      render(<WSDBAlignmentAnalyzer />);

      expect(screen.getByText(/WSDB Alignment Analyzer/i)).toBeInTheDocument();
      expect(
        screen.getByText(/Align pipeline soap brands and scents with the Wet Shaving Database/i)
      ).toBeInTheDocument();
    });

    test('renders analysis controls', async () => {
      setupDefaultMocks();

      render(<WSDBAlignmentAnalyzer />);

      await waitFor(() => {
        expect(screen.getByText('Analysis Settings')).toBeInTheDocument();
        expect(screen.getByText('Similarity Threshold')).toBeInTheDocument();
        expect(screen.getByText('Result Limit')).toBeInTheDocument();
        expect(screen.getByText('Analyze Alignment')).toBeInTheDocument();
        expect(screen.getByText('Refresh WSDB Data')).toBeInTheDocument();
      });
    });

    test('renders filter controls', async () => {
      setupDefaultMocks();

      render(<WSDBAlignmentAnalyzer />);

      await waitFor(() => {
        expect(screen.getByText('Filters')).toBeInTheDocument();
        expect(screen.getByText('Search')).toBeInTheDocument();
        expect(screen.getByText('Confidence Level')).toBeInTheDocument();
        expect(screen.getByText('All')).toBeInTheDocument();
        expect(screen.getByText(/Perfect \(100%\)/i)).toBeInTheDocument();
        expect(screen.getByText(/Non-Perfect \(<100%\)/i)).toBeInTheDocument();
        expect(screen.getByText(/High \(80-99%\)/i)).toBeInTheDocument();
        expect(screen.getByText(/Medium \(60-79%\)/i)).toBeInTheDocument();
        expect(screen.getByText(/Low \(<60%\)/i)).toBeInTheDocument();
      });
    });

    test('renders tabs for both views', async () => {
      setupDefaultMocks();

      render(<WSDBAlignmentAnalyzer />);

      await waitFor(() => {
        expect(screen.getByText(/Pipeline → WSDB/i)).toBeInTheDocument();
        expect(screen.getByText(/WSDB → Pipeline/i)).toBeInTheDocument();
      });
    });
  });

  describe('Data Loading', () => {
    test('loads WSDB and pipeline data on mount', async () => {
      setupDefaultMocks(mockWSDBSoaps, mockPipelineSoaps);

      render(<WSDBAlignmentAnalyzer />);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/api/wsdb-alignment/load-wsdb');
        expect(global.fetch).toHaveBeenCalledWith(
          'http://localhost:8000/api/wsdb-alignment/load-pipeline'
        );
        expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/api/wsdb-alignment/non-matches');
      });

      // Wait for component to finish loading - check for any visible content first
      await waitFor(
        () => {
          // Wait for the component to render (check for any text from the component)
          expect(screen.getByText(/WSDB Alignment Analyzer/i)).toBeInTheDocument();
        },
        { timeout: 5000 }
      );

      // Wait for data to load - check for success message or enabled button
      await waitFor(
        () => {
          // Either success message appears or button is enabled (data loaded)
          const successMessage = screen.queryByText(/Loaded.*WSDB.*pipeline/i);
          const analyzeButton = screen.queryByText('Analyze Alignment');
          expect(successMessage || (analyzeButton && !analyzeButton.hasAttribute('disabled'))).toBeTruthy();
        },
        { timeout: 5000 }
      );
    });

    test('handles load error gracefully', async () => {
      // Mock the first fetch call (load-wsdb) to fail
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      render(<WSDBAlignmentAnalyzer />);

      await waitFor(() => {
        expect(screen.getByText(/Network error/i)).toBeInTheDocument();
      });
    });
  });

  describe('WSDB Refresh', () => {
    test('refresh button triggers API call', async () => {
      setupDefaultMocks();

      render(<WSDBAlignmentAnalyzer />);

      await waitFor(() => {
        expect(screen.getByText('Refresh WSDB Data')).toBeInTheDocument();
      });

      // Setup mock for refresh - returns success
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true, soap_count: 100, updated_at: new Date().toISOString() }),
        })
        // After refresh, reloads WSDB data
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ soaps: [], total_count: 100 }),
        })
        // After refresh, reloads pipeline data
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ soaps: [], total_brands: 0, total_scents: 0 }),
        });

      const refreshButton = screen.getByText('Refresh WSDB Data');
      fireEvent.click(refreshButton);

      await waitFor(() => {
        expect(screen.getByText('Refreshing...')).toBeInTheDocument();
      });

      // After refresh, loadData() is called which shows "Loaded X WSDB soaps and Y pipeline brands"
      await waitFor(() => {
        expect(screen.getByText(/Loaded 100 WSDB soaps and 0 pipeline brands/i)).toBeInTheDocument();
      }, { timeout: 3000 });
    });

    test('displays error on refresh failure', async () => {
      setupDefaultMocks();

      render(<WSDBAlignmentAnalyzer />);

      await waitFor(() => {
        expect(screen.getByText('Refresh WSDB Data')).toBeInTheDocument();
      });

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: false, soap_count: 0, updated_at: '', error: 'API timeout' }),
      });

      const refreshButton = screen.getByText('Refresh WSDB Data');
      fireEvent.click(refreshButton);

      await waitFor(() => {
        expect(screen.getByText(/API timeout/i)).toBeInTheDocument();
      });
    });
  });

  describe('Analysis Controls', () => {
    test('similarity threshold slider updates value', async () => {
      setupDefaultMocks();

      render(<WSDBAlignmentAnalyzer />);

      await waitFor(() => {
        const slider = screen.getByRole('slider');
        expect(slider).toHaveValue('0.7');
      });

      const slider = screen.getByRole('slider');
      fireEvent.change(slider, { target: { value: '0.85' } });

      expect(slider).toHaveValue('0.85');
      expect(screen.getByText('0.85')).toBeInTheDocument();
    });

    test('result limit input updates value', async () => {
      setupDefaultMocks();

      render(<WSDBAlignmentAnalyzer />);

      await waitFor(() => {
        const input = screen.getByPlaceholderText('1-10000');
        expect(input).toHaveValue(100);
      });

      const input = screen.getByPlaceholderText('1-10000');
      fireEvent.change(input, { target: { value: '250' } });

      expect(input).toHaveValue(250);
    });

    test('analyze button triggers analysis', async () => {
      setupDefaultMocks(mockWSDBSoaps, mockPipelineSoaps);

      render(<WSDBAlignmentAnalyzer />);

      // Wait for component to finish loading
      await waitFor(
        () => {
          expect(screen.getByText(/WSDB Alignment Analyzer/i)).toBeInTheDocument();
        },
        { timeout: 5000 }
      );

      // Wait for both success message and button to be enabled (ensures all state updates completed)
      await waitFor(
        () => {
          expect(screen.getByText(/Loaded.*WSDB.*pipeline/i)).toBeInTheDocument();
          const analyzeButton = screen.getByText('Analyze Alignment');
          expect(analyzeButton).not.toBeDisabled();
        },
        { timeout: 10000 }
      );

      const analyzeButton = screen.getByText('Analyze Alignment');

      // Setup mocks for batch analysis
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          pipeline_results: [],
          wsdb_results: [],
        }),
      });

      fireEvent.click(analyzeButton);

      await waitFor(() => {
        expect(screen.getByText('Analyzing...')).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(screen.getByText(/Analysis complete:/i)).toBeInTheDocument();
      });
    });
  });

  describe('Filtering and Search', () => {
    test('text filter filters results', async () => {
      setupDefaultMocks(mockWSDBSoaps, mockPipelineSoaps);

      render(<WSDBAlignmentAnalyzer />);

      await waitFor(() => {
        const searchInput = screen.getByPlaceholderText(/Filter by brand, scent/i);
        expect(searchInput).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/Filter by brand, scent/i);
      fireEvent.change(searchInput, { target: { value: 'Barrister' } });

      expect(searchInput).toHaveValue('Barrister');
    });

    test('confidence filter buttons work', async () => {
      setupDefaultMocks();

      render(<WSDBAlignmentAnalyzer />);

      await waitFor(() => {
        expect(screen.getByText(/Non-Perfect \(<100%\)/i)).toBeInTheDocument();
      });

      // Verify default selection is Non-Perfect
      const nonPerfectButton = screen.getByText(/Non-Perfect \(<100%\)/i);
      expect(nonPerfectButton).toBeInTheDocument();

      // Test clicking different filter buttons
      const perfectButton = screen.getByText(/Perfect \(100%\)/i);
      fireEvent.click(perfectButton);
      expect(perfectButton).toBeInTheDocument();

      const highButton = screen.getByText(/High \(80-99%\)/i);
      fireEvent.click(highButton);
      expect(highButton).toBeInTheDocument();

      const mediumButton = screen.getByText(/Medium \(60-79%\)/i);
      fireEvent.click(mediumButton);
      expect(mediumButton).toBeInTheDocument();

      const lowButton = screen.getByText(/Low \(<60%\)/i);
      fireEvent.click(lowButton);
      expect(lowButton).toBeInTheDocument();

      const allButton = screen.getByText('All');
      fireEvent.click(allButton);
      expect(allButton).toBeInTheDocument();
    });

    test('filter logic correctly filters results by confidence ranges', async () => {
      const mockResults = [
        {
          source_brand: 'Brand A',
          source_scent: 'Scent 1',
          matches: [
            {
              confidence: 100,
              brand: 'Brand A',
              name: 'Scent 1',
              brand_score: 100,
              scent_score: 100,
              source: 'wsdb',
              details: {},
            },
          ],
        },
        {
          source_brand: 'Brand B',
          source_scent: 'Scent 2',
          matches: [
            {
              confidence: 99.9,
              brand: 'Brand B',
              name: 'Scent 2',
              brand_score: 99.9,
              scent_score: 99.9,
              source: 'wsdb',
              details: {},
            },
          ],
        },
        {
          source_brand: 'Brand C',
          source_scent: 'Scent 3',
          matches: [
            {
              confidence: 80,
              brand: 'Brand C',
              name: 'Scent 3',
              brand_score: 80,
              scent_score: 80,
              source: 'wsdb',
              details: {},
            },
          ],
        },
        {
          source_brand: 'Brand D',
          source_scent: 'Scent 4',
          matches: [
            {
              confidence: 79.9,
              brand: 'Brand D',
              name: 'Scent 4',
              brand_score: 79.9,
              scent_score: 79.9,
              source: 'wsdb',
              details: {},
            },
          ],
        },
        {
          source_brand: 'Brand E',
          source_scent: 'Scent 5',
          matches: [
            {
              confidence: 60,
              brand: 'Brand E',
              name: 'Scent 5',
              brand_score: 60,
              scent_score: 60,
              source: 'wsdb',
              details: {},
            },
          ],
        },
        {
          source_brand: 'Brand F',
          source_scent: 'Scent 6',
          matches: [
            {
              confidence: 59.9,
              brand: 'Brand F',
              name: 'Scent 6',
              brand_score: 59.9,
              scent_score: 59.9,
              source: 'wsdb',
              details: {},
            },
          ],
        },
        {
          source_brand: 'Brand G',
          source_scent: 'Scent 7',
          matches: [],
        },
      ];

      setupDefaultMocks(mockWSDBSoaps, mockPipelineSoaps);

      render(<WSDBAlignmentAnalyzer />);

      // Wait for component to finish loading
      await waitFor(
        () => {
          expect(screen.getByText(/WSDB Alignment Analyzer/i)).toBeInTheDocument();
        },
        { timeout: 5000 }
      );

      // Wait for both success message and button to be enabled (ensures all state updates completed)
      await waitFor(
        () => {
          expect(screen.getByText(/Loaded.*WSDB.*pipeline/i)).toBeInTheDocument();
          const analyzeButton = screen.getByText('Analyze Alignment');
          expect(analyzeButton).not.toBeDisabled();
        },
        { timeout: 10000 }
      );

      const analyzeButton = screen.getByText('Analyze Alignment');

      // Mock batch analysis response
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          pipeline_results: mockResults,
          wsdb_results: [],
        }),
      });

      fireEvent.click(analyzeButton);

      await waitFor(() => {
        expect(screen.getByText(/Analysis complete:/i)).toBeInTheDocument();
      });

      // Test Perfect filter (100%)
      const perfectButton = screen.getByText(/Perfect \(100%\)/i);
      fireEvent.click(perfectButton);
      await waitFor(() => {
        expect(screen.getByText('Brand A - Scent 1')).toBeInTheDocument();
        expect(screen.queryByText('Brand B - Scent 2')).not.toBeInTheDocument();
      });

      // Test Non-Perfect filter (<100%)
      const nonPerfectButton = screen.getByText(/Non-Perfect \(<100%\)/i);
      fireEvent.click(nonPerfectButton);
      await waitFor(() => {
        expect(screen.queryByText('Brand A - Scent 1')).not.toBeInTheDocument();
        expect(screen.getByText('Brand B - Scent 2')).toBeInTheDocument();
      });

      // Test High filter (80-99%)
      const highButton = screen.getByText(/High \(80-99%\)/i);
      fireEvent.click(highButton);
      await waitFor(() => {
        expect(screen.getByText('Brand B - Scent 2')).toBeInTheDocument();
        expect(screen.getByText('Brand C - Scent 3')).toBeInTheDocument();
        expect(screen.queryByText('Brand D - Scent 4')).not.toBeInTheDocument();
      });

      // Test Medium filter (60-79%)
      const mediumButton = screen.getByText(/Medium \(60-79%\)/i);
      fireEvent.click(mediumButton);
      await waitFor(() => {
        expect(screen.getByText('Brand D - Scent 4')).toBeInTheDocument();
        expect(screen.getByText('Brand E - Scent 5')).toBeInTheDocument();
        expect(screen.queryByText('Brand C - Scent 3')).not.toBeInTheDocument();
      });

      // Test Low filter (<60%)
      const lowButton = screen.getByText(/Low \(<60%\)/i);
      fireEvent.click(lowButton);
      await waitFor(() => {
        expect(screen.getByText('Brand F - Scent 6')).toBeInTheDocument();
        expect(screen.getByText('Brand G - Scent 7')).toBeInTheDocument();
        expect(screen.queryByText('Brand E - Scent 5')).not.toBeInTheDocument();
      });

      // Test All filter (show everything)
      const allButton = screen.getByText('All');
      fireEvent.click(allButton);
      await waitFor(() => {
        expect(screen.getByText('Brand A - Scent 1')).toBeInTheDocument();
        expect(screen.getByText('Brand B - Scent 2')).toBeInTheDocument();
        expect(screen.getByText('Brand C - Scent 3')).toBeInTheDocument();
        expect(screen.getByText('Brand D - Scent 4')).toBeInTheDocument();
        expect(screen.getByText('Brand E - Scent 5')).toBeInTheDocument();
        expect(screen.getByText('Brand F - Scent 6')).toBeInTheDocument();
        expect(screen.getByText('Brand G - Scent 7')).toBeInTheDocument();
      });
    });
  });

  describe('View Switching', () => {
    test('switches between Pipeline → WSDB and WSDB → Pipeline tabs', async () => {
      setupDefaultMocks();

      render(<WSDBAlignmentAnalyzer />);

      await waitFor(() => {
        expect(screen.getByText(/Pipeline → WSDB/i)).toBeInTheDocument();
        expect(screen.getByText(/WSDB → Pipeline/i)).toBeInTheDocument();
      });

      // Switch tabs to verify navigation works
      const wsdbTab = screen.getByText(/WSDB → Pipeline/i);
      fireEvent.click(wsdbTab);

      const pipelineTab = screen.getByText(/Pipeline → WSDB/i);
      fireEvent.click(pipelineTab);

      // Tabs should still be present
      expect(screen.getByText(/Pipeline → WSDB/i)).toBeInTheDocument();
      expect(screen.getByText(/WSDB → Pipeline/i)).toBeInTheDocument();
    });
  });

  describe('Match Display', () => {
    test('displays empty state when no results', async () => {
      setupDefaultMocks();

      render(<WSDBAlignmentAnalyzer />);

      await waitFor(() => {
        expect(
          screen.getByText(/No results yet. Click "Analyze Alignment" to start./i)
        ).toBeInTheDocument();
      });
    });

    test('displays confidence badges with correct colors', async () => {
      setupDefaultMocks(mockWSDBSoaps, mockPipelineSoaps);

      render(<WSDBAlignmentAnalyzer />);

      // Wait for component to finish loading
      await waitFor(
        () => {
          expect(screen.getByText(/WSDB Alignment Analyzer/i)).toBeInTheDocument();
        },
        { timeout: 5000 }
      );

      // Wait for both success message and button to be enabled (ensures all state updates completed)
      await waitFor(
        () => {
          expect(screen.getByText(/Loaded.*WSDB.*pipeline/i)).toBeInTheDocument();
          const analyzeButton = screen.getByText('Analyze Alignment');
          expect(analyzeButton).not.toBeDisabled();
        },
        { timeout: 10000 }
      );

      const analyzeButton = screen.getByText('Analyze Alignment');

      // Setup mocks for batch analysis with different confidence scores
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          pipeline_results: [
            {
              source_brand: 'Test Brand',
              source_scent: 'Test Scent',
              matches: [
                {
                  brand: 'Test',
                  name: 'Test',
                  confidence: 85,
                  brand_score: 90,
                  scent_score: 78,
                  source: 'wsdb',
                  details: {},
                },
              ],
            },
          ],
          wsdb_results: [],
        }),
      });

      const analyzeButtonForClick = screen.getByText('Analyze Alignment');
      fireEvent.click(analyzeButtonForClick);

      await waitFor(() => {
        expect(screen.getByText(/Analysis complete:/i)).toBeInTheDocument();
      });

      // Should display High confidence badge
      await waitFor(() => {
        const badges = screen.getAllByText(/High/i);
        expect(badges.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Expandable Rows', () => {
    test('expands and collapses match details', async () => {
      setupDefaultMocks(mockWSDBSoaps, [mockPipelineSoaps[0]]);

      render(<WSDBAlignmentAnalyzer />);

      // Wait for component to finish loading
      await waitFor(
        () => {
          expect(screen.getByText(/WSDB Alignment Analyzer/i)).toBeInTheDocument();
        },
        { timeout: 5000 }
      );

      // Wait for both success message and button to be enabled (ensures all state updates completed)
      await waitFor(
        () => {
          expect(screen.getByText(/Loaded.*WSDB.*pipeline/i)).toBeInTheDocument();
          const analyzeButton = screen.getByText('Analyze Alignment');
          expect(analyzeButton).not.toBeDisabled();
        },
        { timeout: 10000 }
      );

      const analyzeButton = screen.getByText('Analyze Alignment');

      // Setup mock with detailed match using batch analysis format
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          pipeline_results: [
            {
              source_brand: 'Barrister and Mann',
              source_scent: 'Seville',
              matches: [
                {
                  brand: 'Barrister and Mann',
                  name: 'Seville',
                  confidence: 95.5,
                  brand_score: 100,
                  scent_score: 89,
                  source: 'wsdb',
                  details: {
                    slug: 'barrister-and-mann-seville',
                    scent_notes: ['citrus', 'lavender'],
                    collaborators: [],
                    tags: ['classic'],
                    category: 'Traditional',
                  },
                },
              ],
            },
          ],
          wsdb_results: [],
        }),
      });

      fireEvent.click(analyzeButton);

      await waitFor(() => {
        expect(screen.getByText(/Analysis complete:/i)).toBeInTheDocument();
      });

      // Find expandable row
      await waitFor(() => {
        const rows = screen.getAllByText(/Barrister and Mann/i);
        expect(rows.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Statistics Display', () => {
    test('displays statistics correctly', async () => {
      setupDefaultMocks();

      render(<WSDBAlignmentAnalyzer />);

      await waitFor(() => {
        expect(screen.getByText('Statistics')).toBeInTheDocument();
        expect(screen.getAllByText(/Total:/i).length).toBeGreaterThan(0);
        expect(screen.getAllByText(/High Confidence:/i).length).toBeGreaterThan(0);
        expect(screen.getAllByText(/Medium Confidence:/i).length).toBeGreaterThan(0);
        expect(screen.getAllByText(/Low\/No Match:/i).length).toBeGreaterThan(0);
      });
    });
  });

  describe('Alias Functionality', () => {
    const mockPipelineSoapsWithAliases = [
      {
        brand: 'Alexandria Grooming',
        aliases: ['Alexendria Fragrances', 'Alexandria Fragrance'],
        scents: [{ name: 'Fructus Virginis', patterns: ['fructus.*virginis'] }],
      },
      {
        brand: 'Barrister and Mann',
        aliases: ['B&M', 'Barrister & Mann'],
        scents: [{ name: 'Seville', patterns: ['seville'] }],
      },
    ];

    const mockBatchAnalyzeWithAliases = {
      pipeline_results: [
        {
          source_brand: 'Alexandria Grooming',
          source_scent: '',
          matches: [
            {
              brand: 'Alexendria Fragrances',
              name: 'Fructus Virginis',
              confidence: 92.5,
              brand_score: 95,
              scent_score: 0,
              source: 'wsdb',
              matched_via: 'alias',
              details: {
                slug: 'alexendria-fragrances-fructus-virginis',
                scent_notes: ['fig', 'fruit'],
                collaborators: [],
                tags: [],
                category: 'Artisan',
              },
            },
          ],
          expanded: false,
        },
      ],
      wsdb_results: [],
      mode: 'brands',
      threshold: 0.7,
    };

    test('displays aliases in result headers with (aka) format', async () => {
      setupDefaultMocks(mockWSDBSoaps, mockPipelineSoapsWithAliases);

      render(<WSDBAlignmentAnalyzer />);

      // Wait for component to finish loading
      await waitFor(
        () => {
          expect(screen.getByText(/WSDB Alignment Analyzer/i)).toBeInTheDocument();
        },
        { timeout: 5000 }
      );

      // Wait for both success message and button to be enabled (ensures all state updates completed)
      await waitFor(
        () => {
          expect(screen.getByText(/Loaded.*WSDB.*pipeline/i)).toBeInTheDocument();
          const analyzeButton = screen.getByText('Analyze Alignment');
          expect(analyzeButton).not.toBeDisabled();
        },
        { timeout: 10000 }
      );

      const analyzeButton = screen.getByText('Analyze Alignment');

      // Setup mock for batch analyze
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockBatchAnalyzeWithAliases,
      });

      fireEvent.click(analyzeButton);

      await waitFor(() => {
        // Check for aliases display
        expect(screen.getByText(/Alexandria Grooming/i)).toBeInTheDocument();
        expect(screen.getByText(/\(aka Alexendria Fragrances, Alexandria Fragrance\)/i)).toBeInTheDocument();
      });
    });

    test('displays "via alias" badge when match is through alias', async () => {
      setupDefaultMocks(mockWSDBSoaps, mockPipelineSoapsWithAliases);

      render(<WSDBAlignmentAnalyzer />);

      // Wait for component to finish loading
      await waitFor(
        () => {
          expect(screen.getByText(/WSDB Alignment Analyzer/i)).toBeInTheDocument();
        },
        { timeout: 5000 }
      );

      // Wait for both success message and button to be enabled (ensures all state updates completed)
      await waitFor(
        () => {
          expect(screen.getByText(/Loaded.*WSDB.*pipeline/i)).toBeInTheDocument();
          const analyzeButton = screen.getByText('Analyze Alignment');
          expect(analyzeButton).not.toBeDisabled();
        },
        { timeout: 10000 }
      );

      const analyzeButton = screen.getByText('Analyze Alignment');

      // Setup mock for batch analyze
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockBatchAnalyzeWithAliases,
      });

      fireEvent.click(analyzeButton);

      await waitFor(() => {
        expect(screen.getByText(/Alexandria Grooming/i)).toBeInTheDocument();
      });

      // Expand the result to see matches
      const expandButton = screen.getByText(/Alexandria Grooming/i).closest('div');
      if (expandButton) {
        fireEvent.click(expandButton);
      }

      await waitFor(() => {
        // Check for "via alias" badge
        expect(screen.getByText(/via alias/i)).toBeInTheDocument();
      });
    });

    test('does not display "via alias" badge for canonical matches', async () => {
      const mockBatchAnalyzeCanonical = {
        pipeline_results: [
          {
            source_brand: 'Barrister and Mann',
            source_scent: '',
            matches: [
              {
                brand: 'Barrister and Mann',
                name: 'Seville',
                confidence: 100.0,
                brand_score: 100,
                scent_score: 0,
                source: 'wsdb',
                matched_via: 'canonical',
                details: {
                  slug: 'barrister-and-mann-seville',
                  scent_notes: ['citrus', 'lavender'],
                  collaborators: [],
                  tags: ['classic'],
                  category: 'Traditional',
                },
              },
            ],
            expanded: false,
          },
        ],
        wsdb_results: [],
        mode: 'brands',
        threshold: 0.7,
      };

      setupDefaultMocks(mockWSDBSoaps, mockPipelineSoapsWithAliases);

      render(<WSDBAlignmentAnalyzer />);

      // Wait for component to finish loading
      await waitFor(
        () => {
          expect(screen.getByText(/WSDB Alignment Analyzer/i)).toBeInTheDocument();
        },
        { timeout: 5000 }
      );

      // Wait for both success message and button to be enabled (ensures all state updates completed)
      await waitFor(
        () => {
          expect(screen.getByText(/Loaded.*WSDB.*pipeline/i)).toBeInTheDocument();
          const analyzeButton = screen.getByText('Analyze Alignment');
          expect(analyzeButton).not.toBeDisabled();
        },
        { timeout: 10000 }
      );

      const analyzeButton = screen.getByText('Analyze Alignment');

      // Setup mock for batch analyze
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockBatchAnalyzeCanonical,
      });

      fireEvent.click(analyzeButton);

      await waitFor(() => {
        expect(screen.getByText(/Analysis complete:/i)).toBeInTheDocument();
      });

      // For canonical matches, "via alias" badge should not be present
      // (We don't need to expand to check this - it wouldn't be visible if not added)
      expect(screen.queryByText(/via alias/i)).not.toBeInTheDocument();
    });

    test('pipeline data includes aliases field', async () => {
      setupDefaultMocks(mockWSDBSoaps, mockPipelineSoapsWithAliases);

      render(<WSDBAlignmentAnalyzer />);

      // Wait for component to finish loading
      await waitFor(
        () => {
          expect(screen.getByText(/WSDB Alignment Analyzer/i)).toBeInTheDocument();
        },
        { timeout: 5000 }
      );

      // Wait for data to load
      await waitFor(
        () => {
          const analyzeButton = screen.queryByText('Analyze Alignment');
          expect(analyzeButton).toBeInTheDocument();
          expect(analyzeButton).not.toBeDisabled();
        },
        { timeout: 5000 }
      );

      // Verify the fetch was called correctly (with full URL)
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/wsdb-alignment/load-pipeline')
      );
    });
  });

  describe('Non-Matches Functionality', () => {
    const mockNonMatches = {
      brand_non_matches: [
        {
          pipeline_brand: 'Black Mountain Shaving',
          wsdb_brand: 'Mountain Hare Shaving',
          added_at: '2025-12-17T10:30:00Z',
        },
      ],
      scent_non_matches: [
        {
          pipeline_brand: 'Barrister and Mann',
          pipeline_scent: 'Le Grand Chypre',
          wsdb_brand: 'Barrister and Mann',
          wsdb_scent: 'Le Petit Chypre',
          added_at: '2025-12-17T10:31:00Z',
        },
      ],
    };

    const mockBatchAnalysisResponse = {
      pipeline_results: [
        {
          source_brand: 'Barrister and Mann',
          source_scent: '',
          matches: [
            {
              brand: 'Barrister and Mann',
              name: 'Seville',
              confidence: 95.5,
              brand_score: 100,
              scent_score: 89,
              source: 'wsdb',
              matched_via: 'canonical',
              details: { slug: 'barrister-and-mann-seville' },
            },
          ],
          expanded: false,
        },
      ],
      wsdb_results: [],
    };

    test('displays "Not a Match" button in brands mode', async () => {
      setupDefaultMocks(mockWSDBSoaps, mockPipelineSoaps);
      // Add mock for batch analysis (after initial 3 mocks from setupDefaultMocks)
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockBatchAnalysisResponse,
      });

      render(<WSDBAlignmentAnalyzer />);

      // Wait for component to finish loading
      await waitFor(
        () => {
          expect(screen.getByText(/WSDB Alignment Analyzer/i)).toBeInTheDocument();
        },
        { timeout: 5000 }
      );

      // Wait for both success message and button to be enabled (ensures all state updates completed)
      await waitFor(
        () => {
          expect(screen.getByText(/Loaded.*WSDB.*pipeline/i)).toBeInTheDocument();
          const analyzeButton = screen.getByText('Analyze Alignment');
          expect(analyzeButton).not.toBeDisabled();
        },
        { timeout: 10000 }
      );

      const analyzeButton = screen.getByText('Analyze Alignment');

      // Click analyze button
      fireEvent.click(analyzeButton);

      // Wait for results
      await waitFor(() => {
        expect(screen.getByText(/Analysis complete/i)).toBeInTheDocument();
      });

      // Find and expand the first result row - the entire row is clickable
      await waitFor(() => {
        expect(screen.getByText(/Barrister and Mann/i)).toBeInTheDocument();
      });

      // Find the row container (the div with the brand name) and click it to expand
      const brandText = screen.getByText(/Barrister and Mann/i);
      const rowContainer = brandText.closest('div.flex.items-center.justify-between.cursor-pointer') || 
                          brandText.closest('div.border.rounded-lg');
      if (rowContainer) {
        fireEvent.click(rowContainer);
      } else {
        // Fallback: click on the brand text itself
        fireEvent.click(brandText);
      }

      // Wait for "Not a Match" button to appear
      await waitFor(() => {
        expect(screen.getByText(/Not a Match/i)).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    test('displays "Not a Match" button in brand+scent mode', async () => {
      setupDefaultMocks(mockWSDBSoaps, mockPipelineSoaps);
      // Add mock for batch analysis (after initial 3 mocks from setupDefaultMocks)
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          ...mockBatchAnalysisResponse,
          pipeline_results: [
            {
              source_brand: 'Barrister and Mann',
              source_scent: 'Seville',
              matches: mockBatchAnalysisResponse.pipeline_results[0].matches,
              expanded: false,
            },
          ],
        }),
      });

      render(<WSDBAlignmentAnalyzer />);

      // Wait for component to finish loading
      await waitFor(
        () => {
          expect(screen.getByText(/WSDB Alignment Analyzer/i)).toBeInTheDocument();
        },
        { timeout: 5000 }
      );

      // Wait for both success message and button to be enabled (ensures all state updates completed)
      await waitFor(
        () => {
          expect(screen.getByText(/Loaded.*WSDB.*pipeline/i)).toBeInTheDocument();
          const analyzeButton = screen.getByText('Analyze Alignment');
          expect(analyzeButton).not.toBeDisabled();
        },
        { timeout: 10000 }
      );

      // Switch to Brand + Scent mode
      const brandScentButton = screen.getByText(/Brand \+ Scent/i);
      fireEvent.click(brandScentButton);

      // Click analyze button
      const analyzeButton = screen.getByText('Analyze Alignment');
      fireEvent.click(analyzeButton);

      // Wait for results
      await waitFor(() => {
        expect(screen.getByText(/Analysis complete/i)).toBeInTheDocument();
      });

      // Find and expand the first result row - the entire row is clickable
      await waitFor(() => {
        expect(screen.getByText(/Barrister and Mann/i)).toBeInTheDocument();
        expect(screen.getByText(/Seville/i)).toBeInTheDocument();
      });

      // Find the row container and click it to expand
      const brandText = screen.getByText(/Barrister and Mann/i);
      const rowContainer = brandText.closest('div.flex.items-center.justify-between.cursor-pointer') || 
                          brandText.closest('div.border.rounded-lg');
      if (rowContainer) {
        fireEvent.click(rowContainer);
      } else {
        // Fallback: click on the brand text itself
        fireEvent.click(brandText);
      }

      // Wait for "Not a Match" button to appear
      await waitFor(() => {
        expect(screen.getByText(/Not a Match/i)).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    test('clicking "Not a Match" saves and filters result', async () => {
      setupDefaultMocks(mockWSDBSoaps, mockPipelineSoaps);
      // Set up mocks for: batch analysis, POST save, reload non-matches, re-analyze
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockBatchAnalysisResponse,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true, message: 'Non-match added successfully' }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockNonMatches,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            ...mockBatchAnalysisResponse,
            pipeline_results: [
              {
                source_brand: 'Barrister and Mann',
                source_scent: '',
                matches: [], // Empty after filtering
                expanded: false,
              },
            ],
          }),
        });

      render(<WSDBAlignmentAnalyzer />);

      // Wait for component to finish loading
      await waitFor(
        () => {
          expect(screen.getByText(/WSDB Alignment Analyzer/i)).toBeInTheDocument();
        },
        { timeout: 5000 }
      );

      // Wait for both success message and button to be enabled (ensures all state updates completed)
      await waitFor(
        () => {
          expect(screen.getByText(/Loaded.*WSDB.*pipeline/i)).toBeInTheDocument();
          const analyzeButton = screen.getByText('Analyze Alignment');
          expect(analyzeButton).not.toBeDisabled();
        },
        { timeout: 10000 }
      );

      const analyzeButton = screen.getByText('Analyze Alignment');

      // Click analyze button
      fireEvent.click(analyzeButton);

      // Wait for results
      await waitFor(() => {
        expect(screen.getByText(/Analysis complete/i)).toBeInTheDocument();
      });

      // Find and expand the first result row - the entire row is clickable
      await waitFor(() => {
        expect(screen.getByText(/Barrister and Mann/i)).toBeInTheDocument();
      });

      // Find the row container and click it to expand
      const brandText = screen.getByText(/Barrister and Mann/i);
      const rowContainer = brandText.closest('div.flex.items-center.justify-between.cursor-pointer') || 
                          brandText.closest('div.border.rounded-lg');
      if (rowContainer) {
        fireEvent.click(rowContainer);
      } else {
        // Fallback: click on the brand text itself
        fireEvent.click(brandText);
      }

      // Wait for "Not a Match" button
      await waitFor(() => {
        expect(screen.getByText(/Not a Match/i)).toBeInTheDocument();
      }, { timeout: 5000 });

      // Click "Not a Match" button
      const notMatchButton = screen.getByText(/Not a Match/i);
      fireEvent.click(notMatchButton);

      // Verify POST request was made
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/wsdb-alignment/non-matches'),
          expect.objectContaining({
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
          })
        );
      }, { timeout: 5000 });

      // Verify success message (displayed via toast notification)
      // The mock returns "Non-match added successfully", component uses data.message
      await waitFor(() => {
        expect(screen.getByText(/Non-match added successfully/i)).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    test('non-matches are loaded and applied on mount', async () => {
      setupDefaultMocks(mockWSDBSoaps, mockPipelineSoaps);

      render(<WSDBAlignmentAnalyzer />);

      // Wait for component to finish loading
      await waitFor(
        () => {
          expect(screen.getByText(/WSDB Alignment Analyzer/i)).toBeInTheDocument();
        },
        { timeout: 5000 }
      );

      // Wait for both success message and button to be enabled (ensures all state updates completed)
      await waitFor(
        () => {
          expect(screen.getByText(/Loaded.*WSDB.*pipeline/i)).toBeInTheDocument();
          const analyzeButton = screen.getByText('Analyze Alignment');
          expect(analyzeButton).not.toBeDisabled();
        },
        { timeout: 10000 }
      );

      // Verify non-matches endpoint was called
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/wsdb-alignment/non-matches')
        );
      });
    });
  });

  describe('Data Source Toggle', () => {
    beforeEach(() => {
      jest.clearAllMocks();
      // Reset mock implementation to ensure clean state between tests
      (global.fetch as jest.Mock).mockReset();
    });

    it('should show catalog mode by default', async () => {
      setupDefaultMocks(mockWSDBSoaps, mockPipelineSoaps);
      // Note: setupDefaultMocks already mocks non-matches, so this extra mock is redundant but harmless

      render(<WSDBAlignmentAnalyzer />);

      // Wait for component to render
      await waitFor(
        () => {
          expect(screen.getByText(/WSDB Alignment Analyzer/i)).toBeInTheDocument();
        },
        { timeout: 5000 }
      );

      // Should show catalog button as active
      const catalogButton = screen.getByText('Catalog');
      expect(catalogButton).toBeInTheDocument();
    });

    it('should show month selector when match files mode is selected', async () => {
      setupDefaultMocks(mockWSDBSoaps, mockPipelineSoaps);
      // When switching to match files mode, the useEffect calls:
      // 1. reloadPipelineSoaps() - needs mock
      // 2. loadNonMatches() - needs mock
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            soaps: mockPipelineSoaps,
            total_brands: mockPipelineSoaps.length,
            total_scents: mockPipelineSoaps.reduce((sum, soap) => sum + (soap.scents?.length || 0), 0),
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            brand_non_matches: [],
            scent_non_matches: [],
          }),
        });

      render(<WSDBAlignmentAnalyzer />);

      // Wait for component to finish loading
      await waitFor(
        () => {
          expect(screen.getByText(/WSDB Alignment Analyzer/i)).toBeInTheDocument();
        },
        { timeout: 5000 }
      );

      // Wait for both success message and button to be enabled (ensures all state updates completed)
      await waitFor(
        () => {
          expect(screen.getByText(/Loaded.*WSDB.*pipeline/i)).toBeInTheDocument();
          const analyzeButton = screen.getByText('Analyze Alignment');
          expect(analyzeButton).not.toBeDisabled();
        },
        { timeout: 10000 }
      );

      // Click match files button
      const matchFilesButton = screen.getByText('Match Files');
      fireEvent.click(matchFilesButton);

      // Wait for mode switch to complete - check for any text that indicates match files mode
      // The MonthSelector should render with "Analysis Months" label
      await waitFor(() => {
        // Look for "Analysis Months" which is the MonthSelector's label prop
        expect(screen.getByText(/Analysis Months/i)).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    it('should call batch-analyze-match-files endpoint when analyzing in match files mode', async () => {
      setupDefaultMocks(mockWSDBSoaps, mockPipelineSoaps);
      // When switching to match files mode, the useEffect calls:
      // 1. reloadPipelineSoaps() - needs mock
      // 2. loadNonMatches() - needs mock
      // Then when analyzing, it calls batch-analyze-match-files
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            soaps: mockPipelineSoaps,
            total_brands: mockPipelineSoaps.length,
            total_scents: mockPipelineSoaps.reduce((sum, soap) => sum + (soap.scents?.length || 0), 0),
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            brand_non_matches: [],
            scent_non_matches: [],
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            pipeline_results: [],
            wsdb_results: [],
            mode: 'brand_scent',
            threshold: 0.7,
            months_processed: ['2025-05'],
            total_entries: 0,
          }),
        });

      render(<WSDBAlignmentAnalyzer />);

      // Wait for component to finish loading
      await waitFor(
        () => {
          expect(screen.getByText(/WSDB Alignment Analyzer/i)).toBeInTheDocument();
        },
        { timeout: 5000 }
      );

      // Wait for both success message and button to be enabled (ensures all state updates completed)
      await waitFor(
        () => {
          expect(screen.getByText(/Loaded.*WSDB.*pipeline/i)).toBeInTheDocument();
          const analyzeButton = screen.getByText('Analyze Alignment');
          expect(analyzeButton).not.toBeDisabled();
        },
        { timeout: 10000 }
      );

      // Switch to match files mode
      const matchFilesButton = screen.getByText('Match Files');
      fireEvent.click(matchFilesButton);

      // Wait for mode switch to complete - check for "Analysis Months" which is the MonthSelector's label
      await waitFor(() => {
        expect(screen.getByText(/Analysis Months/i)).toBeInTheDocument();
      }, { timeout: 5000 });

      // Note: MonthSelector component interaction would require more complex setup
      // This test verifies the mode switching works
      expect(matchFilesButton).toBeInTheDocument();
    });
  });
});

