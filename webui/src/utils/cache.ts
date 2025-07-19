interface CacheEntry<T> {
    data: T;
    timestamp: number;
    ttl: number;
}

interface CacheOptions {
    ttl?: number; // Time to live in milliseconds
    maxSize?: number; // Maximum number of entries
}

class Cache<T> {
    private cache = new Map<string, CacheEntry<T>>();
    private readonly ttl: number;
    private readonly maxSize: number;

    constructor(options: CacheOptions = {}) {
        this.ttl = options.ttl || 5 * 60 * 1000; // 5 minutes default
        this.maxSize = options.maxSize || 100; // 100 entries default
    }

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

    has(key: string): boolean {
        return this.get(key) !== null;
    }

    delete(key: string): boolean {
        return this.cache.delete(key);
    }

    clear(): void {
        this.cache.clear();
    }

    size(): number {
        this.cleanup();
        return this.cache.size;
    }

    private cleanup(): void {
        const now = Date.now();
        for (const [key, entry] of this.cache.entries()) {
            if (now - entry.timestamp > entry.ttl) {
                this.cache.delete(key);
            }
        }
    }

    getStats(): { size: number; maxSize: number; hitRate: number } {
        return {
            size: this.size(),
            maxSize: this.maxSize,
            hitRate: 0, // Would need to track hits/misses for this
        };
    }
}

// Analysis result cache
export const analysisCache = new Cache<any>({
    ttl: 10 * 60 * 1000, // 10 minutes for analysis results
    maxSize: 50, // 50 cached analyses
});

// Catalog cache
export const catalogCache = new Cache<any>({
    ttl: 30 * 60 * 1000, // 30 minutes for catalogs
    maxSize: 20, // 20 cached catalogs
});

// File data cache
export const fileCache = new Cache<any>({
    ttl: 5 * 60 * 1000, // 5 minutes for file data
    maxSize: 100, // 100 cached files
});

// Cache key generators
export const generateAnalysisKey = (field: string, months: string[], limit?: number): string => {
    return `analysis:${field}:${months.sort().join(',')}:${limit || 'all'}`;
};

export const generateCatalogKey = (catalogName: string): string => {
    return `catalog:${catalogName}`;
};

export const generateFileKey = (month: string): string => {
    return `file:${month}`;
};

// Cache utilities
export const clearAllCaches = (): void => {
    analysisCache.clear();
    catalogCache.clear();
    fileCache.clear();
};

export const getCacheStats = () => {
    return {
        analysis: analysisCache.getStats(),
        catalog: catalogCache.getStats(),
        file: fileCache.getStats(),
    };
};

export default Cache; 