/**
 * Tests for WSDB lookup utility with alias support.
 */

import { getWsdbSlug, WSDBSoap, PipelineSoap } from '../wsdbLookup';

describe('getWsdbSlug', () => {
  const mockWsdbSoaps: WSDBSoap[] = [
    {
      brand: 'Barrister and Mann',
      name: 'Seville',
      slug: 'barrister-and-mann-seville',
    },
    {
      brand: 'The Artisan Shave Shoppe',
      name: 'Crisp Vetiver',
      slug: 'artisan-shave-shoppe-crisp-vetiver',
    },
    {
      brand: 'Stirling Soap Co.',
      name: 'Executive Man',
      slug: 'stirling-soap-co-executive-man',
    },
    {
      brand: 'Stirling Soap Co.',
      name: 'Executive Man Scent',
      slug: 'stirling-executive-man-scent',
    },
  ];

  const mockPipelineSoaps: PipelineSoap[] = [
    {
      brand: 'Barrister and Mann',
      scents: [
        {
          name: 'Seville',
          patterns: ['seville'],
        },
      ],
    },
    {
      brand: 'The Artisan Soap Shoppe',
      aliases: ['The Artisan Shave Shoppe'],
      scents: [
        {
          name: 'Crisp Vetiver',
          patterns: ['crisp.*vetiver'],
        },
      ],
    },
    {
      brand: 'Stirling Soap Co.',
      scents: [
        {
          name: 'Executive Man',
          alias: 'Executive Man Scent',
          patterns: ['executive.*man'],
        },
      ],
    },
  ];

  it('should match canonical brand and scent', () => {
    const slug = getWsdbSlug('Barrister and Mann', 'Seville', mockWsdbSoaps, mockPipelineSoaps);
    expect(slug).toBe('barrister-and-mann-seville');
  });

  it('should match via brand alias', () => {
    // "The Artisan Soap Shoppe" has alias "The Artisan Shave Shoppe"
    // WSDB has "The Artisan Shave Shoppe" - should match via alias
    const slug = getWsdbSlug('The Artisan Soap Shoppe', 'Crisp Vetiver', mockWsdbSoaps, mockPipelineSoaps);
    expect(slug).toBe('artisan-shave-shoppe-crisp-vetiver');
  });

  it('should match via scent alias when canonical does not exist', () => {
    // "Stirling Soap Co." has scent "Executive Man" with alias "Executive Man Scent"
    // Remove canonical entry to test alias matching
    const wsdbSoapsWithoutCanonical = mockWsdbSoaps.filter(
      soap => !(soap.brand === 'Stirling Soap Co.' && soap.name === 'Executive Man')
    );
    const slug = getWsdbSlug('Stirling Soap Co.', 'Executive Man', wsdbSoapsWithoutCanonical, mockPipelineSoaps);
    // Should match the alias entry
    expect(slug).toBe('stirling-executive-man-scent');
  });

  it('should return null when no match is found', () => {
    const slug = getWsdbSlug('Unknown Brand', 'Unknown Scent', mockWsdbSoaps, mockPipelineSoaps);
    expect(slug).toBeNull();
  });

  it('should return null when brand is empty', () => {
    const slug = getWsdbSlug('', 'Seville', mockWsdbSoaps, mockPipelineSoaps);
    expect(slug).toBeNull();
  });

  it('should return null when scent is empty', () => {
    const slug = getWsdbSlug('Barrister and Mann', '', mockWsdbSoaps, mockPipelineSoaps);
    expect(slug).toBeNull();
  });

  it('should return null when wsdbSoaps is empty', () => {
    const slug = getWsdbSlug('Barrister and Mann', 'Seville', [], mockPipelineSoaps);
    expect(slug).toBeNull();
  });

  it('should work with empty pipeline soaps (canonical match only)', () => {
    const slug = getWsdbSlug('Barrister and Mann', 'Seville', mockWsdbSoaps, []);
    expect(slug).toBe('barrister-and-mann-seville');
  });

  it('should be case-insensitive', () => {
    expect(getWsdbSlug('barrister and mann', 'seville', mockWsdbSoaps, mockPipelineSoaps)).toBe(
      'barrister-and-mann-seville'
    );
    expect(getWsdbSlug('BARRISTER AND MANN', 'SEVILLE', mockWsdbSoaps, mockPipelineSoaps)).toBe(
      'barrister-and-mann-seville'
    );
    expect(getWsdbSlug('Barrister And Mann', 'Seville', mockWsdbSoaps, mockPipelineSoaps)).toBe(
      'barrister-and-mann-seville'
    );
  });

  it('should handle brands without aliases', () => {
    const slug = getWsdbSlug('Barrister and Mann', 'Seville', mockWsdbSoaps, mockPipelineSoaps);
    expect(slug).toBe('barrister-and-mann-seville');
  });

  it('should handle scents without aliases', () => {
    const slug = getWsdbSlug('Barrister and Mann', 'Seville', mockWsdbSoaps, mockPipelineSoaps);
    expect(slug).toBe('barrister-and-mann-seville');
  });

  it('should match via both brand alias and scent alias when canonical does not exist', () => {
    // Remove canonical entry first
    const wsdbSoapsWithoutCanonical = mockWsdbSoaps.filter(
      soap => !(soap.brand === 'The Artisan Shave Shoppe' && soap.name === 'Crisp Vetiver')
    );

    // Add a WSDB entry that matches both aliases
    const extendedWsdbSoaps: WSDBSoap[] = [
      ...wsdbSoapsWithoutCanonical,
      {
        brand: 'The Artisan Shave Shoppe', // Brand alias
        name: 'Crisp Vetiver Alias', // Scent alias (if we add it)
        slug: 'artisan-shave-shoppe-crisp-vetiver-alias',
      },
    ];

    // Add scent alias to pipeline
    const extendedPipelineSoaps: PipelineSoap[] = mockPipelineSoaps.map(p => {
      if (p.brand === 'The Artisan Soap Shoppe') {
        return {
          ...p,
          scents: p.scents.map(s => {
            if (s.name === 'Crisp Vetiver') {
              return { ...s, alias: 'Crisp Vetiver Alias' };
            }
            return s;
          }),
        };
      }
      return p;
    });

    const slug = getWsdbSlug('The Artisan Soap Shoppe', 'Crisp Vetiver', extendedWsdbSoaps, extendedPipelineSoaps);
    expect(slug).toBe('artisan-shave-shoppe-crisp-vetiver-alias');
  });

  describe('virtual alias (stripped "soap")', () => {
    it('should match brand with trailing "Soap" to WSDB without "Soap"', () => {
      const wsdbSoaps: WSDBSoap[] = [
        {
          brand: 'Talbot Shaving',
          name: 'Gates of the Arctic',
          slug: 'talbot-shaving-gates-of-the-arctic',
        },
      ];
      const pipelineSoaps: PipelineSoap[] = [
        {
          brand: 'Talbot Shaving Soap',
          scents: [
            {
              name: 'Gates of the Arctic',
              patterns: ['gates.*arctic'],
            },
          ],
        },
      ];
      const slug = getWsdbSlug('Talbot Shaving Soap', 'Gates of the Arctic', wsdbSoaps, pipelineSoaps);
      expect(slug).toBe('talbot-shaving-gates-of-the-arctic');
    });

    it('should match scent with trailing "Soap" to WSDB without "Soap"', () => {
      const wsdbSoaps: WSDBSoap[] = [
        {
          brand: 'Barrister and Mann',
          name: 'Gates of the Arctic',
          slug: 'barrister-and-mann-gates-of-the-arctic',
        },
      ];
      const pipelineSoaps: PipelineSoap[] = [
        {
          brand: 'Barrister and Mann',
          scents: [
            {
              name: 'Gates of the Arctic Soap',
              patterns: ['gates.*arctic'],
            },
          ],
        },
      ];
      const slug = getWsdbSlug('Barrister and Mann', 'Gates of the Arctic Soap', wsdbSoaps, pipelineSoaps);
      expect(slug).toBe('barrister-and-mann-gates-of-the-arctic');
    });

    it('should match both brand and scent with trailing "Soap"', () => {
      const wsdbSoaps: WSDBSoap[] = [
        {
          brand: 'Talbot Shaving',
          name: 'Gates of the Arctic',
          slug: 'talbot-shaving-gates-of-the-arctic',
        },
      ];
      const pipelineSoaps: PipelineSoap[] = [
        {
          brand: 'Talbot Shaving Soap',
          scents: [
            {
              name: 'Gates of the Arctic Soap',
              patterns: ['gates.*arctic'],
            },
          ],
        },
      ];
      const slug = getWsdbSlug('Talbot Shaving Soap', 'Gates of the Arctic Soap', wsdbSoaps, pipelineSoaps);
      expect(slug).toBe('talbot-shaving-gates-of-the-arctic');
    });

    it('should match WSDB entry with "Soap" to pipeline without "Soap"', () => {
      const wsdbSoaps: WSDBSoap[] = [
        {
          brand: 'Test Brand Soap',
          name: 'Test Scent',
          slug: 'test-brand-soap-test-scent',
        },
      ];
      const pipelineSoaps: PipelineSoap[] = [
        {
          brand: 'Test Brand',
          scents: [
            {
              name: 'Test Scent',
              patterns: ['test.*scent'],
            },
          ],
        },
      ];
      const slug = getWsdbSlug('Test Brand', 'Test Scent', wsdbSoaps, pipelineSoaps);
      expect(slug).toBe('test-brand-soap-test-scent');
    });

    it('should be case-insensitive for "soap" stripping', () => {
      const wsdbSoaps: WSDBSoap[] = [
        {
          brand: 'Test Brand',
          name: 'Test Scent',
          slug: 'test-brand-test-scent',
        },
      ];
      const pipelineSoaps: PipelineSoap[] = [
        {
          brand: 'Test Brand Soap',
          scents: [
            {
              name: 'Test Scent',
              patterns: ['test.*scent'],
            },
          ],
        },
      ];
      expect(getWsdbSlug('Test Brand Soap', 'Test Scent', wsdbSoaps, pipelineSoaps)).toBe('test-brand-test-scent');
      expect(getWsdbSlug('Test Brand SOAP', 'Test Scent', wsdbSoaps, pipelineSoaps)).toBe('test-brand-test-scent');
      expect(getWsdbSlug('Test Brand', 'Test Scent Soap', wsdbSoaps, pipelineSoaps)).toBe('test-brand-test-scent');
      expect(getWsdbSlug('Test Brand', 'Test Scent SOAP', wsdbSoaps, pipelineSoaps)).toBe('test-brand-test-scent');
    });

    it('should only strip "soap" when at the end, not in the middle', () => {
      const wsdbSoaps: WSDBSoap[] = [
        {
          brand: 'Soap Company',
          name: 'Test Scent',
          slug: 'soap-company-test-scent',
        },
      ];
      const pipelineSoaps: PipelineSoap[] = [
        {
          brand: 'Soap Company',
          scents: [
            {
              name: 'Test Scent',
              patterns: ['test.*scent'],
            },
          ],
        },
      ];
      // "Soap" is in the middle - should not be stripped, should match directly
      expect(getWsdbSlug('Soap Company', 'Test Scent', wsdbSoaps, pipelineSoaps)).toBe('soap-company-test-scent');
      // But "Soap Company Soap" should match "Soap Company" (stripping trailing "Soap")
      const pipelineSoapsWithSoap: PipelineSoap[] = [
        {
          brand: 'Soap Company Soap',
          scents: [
            {
              name: 'Test Scent',
              patterns: ['test.*scent'],
            },
          ],
        },
      ];
      expect(getWsdbSlug('Soap Company Soap', 'Test Scent', wsdbSoaps, pipelineSoapsWithSoap)).toBe(
        'soap-company-test-scent'
      );
    });
  });

  describe('virtual pattern: accent normalization', () => {
    it('should match accented characters to non-accented', () => {
      const wsdbSoaps: WSDBSoap[] = [
        {
          brand: 'Cafe',
          name: 'Espresso',
          slug: 'cafe-espresso',
        },
      ];
      const pipelineSoaps: PipelineSoap[] = [
        {
          brand: 'Café',
          scents: [
            {
              name: 'Espresso',
              patterns: ['espresso'],
            },
          ],
        },
      ];
      const slug = getWsdbSlug('Café', 'Espresso', wsdbSoaps, pipelineSoaps);
      expect(slug).toBe('cafe-espresso');
    });

    it('should match non-accented to accented characters', () => {
      const wsdbSoaps: WSDBSoap[] = [
        {
          brand: 'Café',
          name: 'Résumé',
          slug: 'cafe-resume',
        },
      ];
      const pipelineSoaps: PipelineSoap[] = [
        {
          brand: 'Cafe',
          scents: [
            {
              name: 'Resume',
              patterns: ['resume'],
            },
          ],
        },
      ];
      const slug = getWsdbSlug('Cafe', 'Resume', wsdbSoaps, pipelineSoaps);
      expect(slug).toBe('cafe-resume');
    });
  });

  describe('virtual pattern: "and" vs "&" normalization', () => {
    it('should match "and" to "&"', () => {
      const wsdbSoaps: WSDBSoap[] = [
        {
          brand: 'Barrister and Mann',
          name: 'Seville',
          slug: 'barrister-and-mann-seville',
        },
      ];
      const pipelineSoaps: PipelineSoap[] = [
        {
          brand: 'Barrister & Mann',
          scents: [
            {
              name: 'Seville',
              patterns: ['seville'],
            },
          ],
        },
      ];
      const slug = getWsdbSlug('Barrister & Mann', 'Seville', wsdbSoaps, pipelineSoaps);
      expect(slug).toBe('barrister-and-mann-seville');
    });

    it('should match "&" to "and"', () => {
      const wsdbSoaps: WSDBSoap[] = [
        {
          brand: 'Test & Company',
          name: 'Scent',
          slug: 'test-and-company-scent',
        },
      ];
      const pipelineSoaps: PipelineSoap[] = [
        {
          brand: 'Test and Company',
          scents: [
            {
              name: 'Scent',
              patterns: ['scent'],
            },
          ],
        },
      ];
      const slug = getWsdbSlug('Test and Company', 'Scent', wsdbSoaps, pipelineSoaps);
      expect(slug).toBe('test-and-company-scent');
    });
  });

  describe('virtual patterns: combined variations', () => {
    it('should handle combinations of all virtual patterns', () => {
      const wsdbSoaps: WSDBSoap[] = [
        {
          brand: 'Cafe',
          name: 'Espresso',
          slug: 'cafe-espresso',
        },
        {
          brand: 'Barrister and Mann',
          name: 'Seville',
          slug: 'barrister-and-mann-seville',
        },
      ];
      const pipelineSoaps: PipelineSoap[] = [
        {
          brand: 'Café Soap',
          scents: [
            {
              name: 'Espresso Soap',
              patterns: ['espresso'],
            },
          ],
        },
        {
          brand: 'Barrister & Mann Soap',
          scents: [
            {
              name: 'Seville',
              patterns: ['seville'],
            },
          ],
        },
      ];
      expect(getWsdbSlug('Café Soap', 'Espresso Soap', wsdbSoaps, pipelineSoaps)).toBe('cafe-espresso');
      expect(getWsdbSlug('Barrister & Mann Soap', 'Seville', wsdbSoaps, pipelineSoaps)).toBe(
        'barrister-and-mann-seville'
      );
    });
  });
});

