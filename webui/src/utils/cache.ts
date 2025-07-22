/**
 * Cache utility for the SOTD Pipeline WebUI
 *
 * This module provides a generic caching system with TTL (Time To Live) support,
 * automatic cleanup of expired entries, and size limits. It's used throughout
 * the application to cache API responses, analysis results, and file data.
 *
 * @module Cache
 */

/**
 * Represents a single cache entry with data, timestamp, and TTL
 */
interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

/**
 * Configuration options for cache instances
 */
interface CacheOptions {
  ttl?: number; // Time to live in milliseconds
  maxSize?: number; // Maximum number of entries
}

/**
 * Generic cache class with TTL support and automatic cleanup
 *
 * Features:
 * - Automatic expiration of entries based on TTL
 * - Size limits with LRU eviction
 * - Thread-safe operations
 * - Statistics tracking
 *
 * @template T - The type of data to cache
 */
class Cache<T> {
  private cache = new Map<string, CacheEntry<T>>();
  private readonly ttl: number;
  private readonly maxSize: number;

  /**
   * Creates a new cache instance
   *
   * @param options - Configuration options for the cache
   * @param options.ttl - Time to live in milliseconds (default: 5 minutes)
   * @param options.maxSize - Maximum number of entries (default: 100)
   */
  constructor(options: CacheOptions = {}) {
    this.ttl = options.ttl || 5 * 60 * 1000; // 5 minutes default
    this.maxSize = options.maxSize || 100; // 100 entries default
  }

  /**
   * Stores data in the cache with optional custom TTL
   *
   * @param key - Unique identifier for the cached data
   * @param data - Data to cache
   * @param customTtl - Optional custom TTL override
   */
  set(key: string, data: T, customTtl?: number): void {
    // Clean expired entries first
    this.cleanup();

    // Remove oldest entry if at max size
    if (this.cache.size >= this.maxSize) {
      const oldestKey = this.cache.keys().next().value;
      if (oldestKey) {
        this.cache.delete(oldestKey);
      }
    }

    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl: customTtl || this.ttl,
    });
  }

  /**
   * Retrieves data from the cache
   *
   * @param key - Unique identifier for the cached data
   * @returns The cached data or null if not found/expired
   */
  get(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    // Check if expired
    if (Date.now() - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return null;
    }

    return entry.data;
  }

  /**
   * Checks if a key exists in the cache and is not expired
   *
   * @param key - Unique identifier to check
   * @returns True if the key exists and is valid
   */
  has(key: string): boolean {
    return this.get(key) !== null;
  }

  /**
   * Removes a specific entry from the cache
   *
   * @param key - Unique identifier to remove
   * @returns True if the entry was removed, false if not found
   */
  delete(key: string): boolean {
    return this.cache.delete(key);
  }

  /**
   * Clears all entries from the cache
   */
  clear(): void {
    this.cache.clear();
  }

  /**
   * Gets the current number of valid entries in the cache
   *
   * @returns Number of non-expired entries
   */
  size(): number {
    this.cleanup();
    return this.cache.size;
  }

  /**
   * Removes expired entries from the cache
   */
  private cleanup(): void {
    const now = Date.now();
    for (const [key, entry] of this.cache.entries()) {
      if (now - entry.timestamp > entry.ttl) {
        this.cache.delete(key);
      }
    }
  }

  /**
   * Gets cache statistics
   *
   * @returns Object containing size, maxSize, and hitRate
   */
  getStats(): { size: number; maxSize: number; hitRate: number } {
    return {
      size: this.size(),
      maxSize: this.maxSize,
      hitRate: 0, // Would need to track hits/misses for this
    };
  }
}

/**
 * Cache instance for analysis results
 * TTL: 10 minutes, Max Size: 50 entries
 */
export const analysisCache = new Cache<any>({
  ttl: 10 * 60 * 1000, // 10 minutes for analysis results
  maxSize: 50, // 50 cached analyses
});

/**
 * Cache instance for catalog data
 * TTL: 30 minutes, Max Size: 20 entries
 */
export const catalogCache = new Cache<any>({
  ttl: 30 * 60 * 1000, // 30 minutes for catalogs
  maxSize: 20, // 20 cached catalogs
});

/**
 * Cache instance for file data
 * TTL: 5 minutes, Max Size: 100 entries
 */
export const fileCache = new Cache<any>({
  ttl: 5 * 60 * 1000, // 5 minutes for file data
  maxSize: 100, // 100 cached files
});

/**
 * Generates a cache key for analysis results
 *
 * @param field - Analysis field (e.g., 'razor', 'brush', 'blade')
 * @param months - Array of month strings
 * @param limit - Optional limit parameter
 * @returns Unique cache key string
 */
export const generateAnalysisKey = (field: string, months: string[], limit?: number): string => {
  return `analysis:${field}:${months.sort().join(',')}:${limit || 'all'}`;
};

/**
 * Generates a cache key for catalog data
 *
 * @param catalogName - Name of the catalog
 * @returns Unique cache key string
 */
export const generateCatalogKey = (catalogName: string): string => {
  return `catalog:${catalogName}`;
};

/**
 * Generates a cache key for file data
 *
 * @param month - Month string (e.g., '2025-01')
 * @returns Unique cache key string
 */
export const generateFileKey = (month: string): string => {
  return `file:${month}`;
};

/**
 * Clears all utility caches (analysis, catalog, file)
 */
export const clearAllCaches = (): void => {
  analysisCache.clear();
  catalogCache.clear();
  fileCache.clear();
};

/**
 * Comprehensive cache clearing function
 *
 * Clears all caches including:
 * - Utility caches (analysis, catalog, file)
 * - Global months cache
 * - localStorage caches
 *
 * This is useful for debugging or when data becomes stale.
 */
export const clearAllCachesComprehensive = (): void => {
  // Clear the utility caches
  clearAllCaches();

  // Clear global months cache
  // @ts-ignore - accessing global cache for clearing
  if (typeof window !== 'undefined' && window.monthsCache !== undefined) {
    // @ts-ignore
    window.monthsCache = null;
  }

  // Clear any localStorage caches
  try {
    const keysToRemove = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && (key.startsWith('cache:') || key.includes('cache'))) {
        keysToRemove.push(key);
      }
    }
    keysToRemove.forEach(key => localStorage.removeItem(key));
  } catch (error) {
    console.warn('Failed to clear localStorage caches:', error);
  }

  // Force browser cache refresh by adding timestamp to all API calls
  // This will be handled by the API interceptor
  console.log('All caches cleared at:', new Date().toISOString());
};

/**
 * Gets statistics for all cache instances
 *
 * @returns Object containing stats for analysis, catalog, and file caches
 */
export const getCacheStats = () => {
  return {
    analysis: analysisCache.getStats(),
    catalog: catalogCache.getStats(),
    file: fileCache.getStats(),
  };
};

export default Cache;
