export interface Product {
  key: string;
  brand: string;
  model: string;
  usage_count: number;
  unique_users: number;
}

export interface UserProductUsage {
  username: string;
  usage_count: number;
  usage_dates: string[];
  comment_ids: string[];
}

export interface ProductUsageAnalysis {
  product: {
    type: string;
    brand: string;
    model: string;
  };
  total_usage: number;
  unique_users: number;
  users: UserProductUsage[];
  usage_by_date: Record<string, string[]>;
  comments_by_date: Record<string, string[]>;
}

