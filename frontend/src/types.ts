export interface User {
  id: number;
  email: string;
  display_name: string;
  created_at?: string | null;
}

export interface Subscription {
  id: number;
  name: string;
  description: string;
  predefined_id?: string | null;
  search_queries: string[];
  active: boolean;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface PredefinedTopic {
  id: string;
  name: string;
  description: string;
  search_queries: string[];
}

export interface ResearchRun {
  id: number;
  subscription_id: number;
  status: string;
  attempt: number;
  started_at?: string | null;
  completed_at?: string | null;
  error_message?: string | null;
  output_path?: string | null;
  documents_found: number;
}

export interface SourceDocument {
  title: string;
  url: string;
  source_type: string;
  origin: string;
  published_at?: string | null;
  content_snippet: string;
}

export interface RunOutput {
  run: ResearchRun;
  markdown: string;
}
