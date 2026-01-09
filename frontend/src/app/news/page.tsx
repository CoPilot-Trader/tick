'use client';

import { useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, Newspaper, ChevronDown, Loader2, AlertCircle, CheckCircle2, Clock, Database, Brain, BarChart3, TrendingUp, TrendingDown, Minus, ExternalLink, FileText } from 'lucide-react';
import { SP500_STOCKS } from '@/lib/mockData';

// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_ENDPOINT = `${API_BASE_URL}/api/v1/news-pipeline/visualize`;

// Types
interface PipelineStep {
  agent: string;
  status: 'completed' | 'processing' | 'error';
  duration_ms?: number;
  start_time?: string;
  error?: string;
  details?: Record<string, any>;
}

interface FinalResult {
  symbol: string;
  aggregated_sentiment: number;
  sentiment_label: 'positive' | 'negative' | 'neutral';
  confidence: number;
  impact: 'High' | 'Medium' | 'Low';
  news_count: number;
  time_weighted: boolean;
  message?: string;
}

interface Article {
  id?: string;
  title: string;
  source: string;
  published_at: string;
  url?: string;
  summary?: string;
  content?: string;
  relevance_score?: number;
}

interface PipelineResponse {
  input: {
    symbol: string;
    min_relevance: number;
    max_articles: number;
    time_horizon: string;
    timestamp: string;
  };
  steps: PipelineStep[];
  final_result: FinalResult | null;
  total_duration_ms: number;
  status: 'success' | 'error';
  error?: string;
}

export default function NewsPage() {
  const [selectedSymbol, setSelectedSymbol] = useState('AAPL');
  const [minRelevance, setMinRelevance] = useState(0.3);
  const [maxArticles, setMaxArticles] = useState(10);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pipelineData, setPipelineData] = useState<PipelineResponse | null>(null);

  const handleProcess = async () => {
    setLoading(true);
    setError(null);
    setPipelineData(null);

    try {
      const response = await fetch(API_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          symbol: selectedSymbol,
          min_relevance: minRelevance,
          max_articles: maxArticles,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: PipelineResponse = await response.json();

      if (data.status === 'error') {
        setError(data.error || 'An error occurred while processing the pipeline');
      } else {
        setPipelineData(data);
      }
    } catch (err) {
      setError(`Failed to connect to backend: ${err instanceof Error ? err.message : 'Unknown error'}. Make sure the backend is running on ${API_BASE_URL}`);
    } finally {
      setLoading(false);
    }
  };

  const getAgentIcon = (agent: string) => {
    switch (agent) {
      case 'news_fetch_agent':
        return <Database className="w-5 h-5" />;
      case 'llm_sentiment_agent':
        return <Brain className="w-5 h-5" />;
      case 'sentiment_aggregator':
        return <BarChart3 className="w-5 h-5" />;
      default:
        return <Newspaper className="w-5 h-5" />;
    }
  };

  const getAgentName = (agent: string) => {
    switch (agent) {
      case 'news_fetch_agent':
        return 'News Fetch Agent';
      case 'llm_sentiment_agent':
        return 'LLM Sentiment Agent';
      case 'sentiment_aggregator':
        return 'Sentiment Aggregator';
      default:
        return agent;
    }
  };

  const getSentimentIcon = (label: string) => {
    switch (label) {
      case 'positive':
        return <TrendingUp className="w-6 h-6 text-success-400" />;
      case 'negative':
        return <TrendingDown className="w-6 h-6 text-danger-400" />;
      default:
        return <Minus className="w-6 h-6 text-gray-400" />;
    }
  };

  const getSentimentColor = (label: string) => {
    switch (label) {
      case 'positive':
        return 'text-success-400';
      case 'negative':
        return 'text-danger-400';
      default:
        return 'text-gray-400';
    }
  };

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'High':
        return 'bg-danger-500/20 text-danger-400 border-danger-500/50';
      case 'Medium':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/50';
      default:
        return 'bg-gray-500/20 text-gray-400 border-gray-500/50';
    }
  };

  // Extract articles from pipeline data
  const getArticles = (): Article[] => {
    if (!pipelineData) return [];
    const newsStep = pipelineData.steps.find(s => s.agent === 'news_fetch_agent');
    if (!newsStep?.details?.final_articles) return [];
    return newsStep.details.final_articles as Article[];
  };

  const articles = getArticles();

  return (
    <div className="min-h-screen w-full bg-gray-950 overflow-y-auto overflow-x-hidden">
      {/* Header */}
      <header className="bg-gray-900 border-b border-gray-800 px-4 py-2 sticky top-0 z-50">
        <div className="flex items-center justify-between gap-4 max-w-7xl mx-auto">
          <div className="flex items-center gap-4">
            <Link
              href="/"
              className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              <span className="text-sm">Dashboard</span>
            </Link>
            <div className="h-4 w-px bg-gray-700" />
            <div className="flex items-center gap-2">
              <Newspaper className="w-5 h-5 text-primary-500" />
              <h1 className="text-lg font-bold text-white">News & Sentiment</h1>
            </div>
          </div>
          <div className="flex-shrink-0">
            <p className="text-xs text-gray-400 hidden sm:block">TICK - News Pipeline Visualizer</p>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="w-full p-4 md:p-6 pb-12">
        {/* Input Section - Full Width */}
        <div className="max-w-[1800px] mx-auto mb-6">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 md:p-6">
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
            Pipeline Configuration
          </h2>
          <div className="flex flex-wrap items-end gap-4">
            {/* Stock Selector */}
            <div className="relative flex-1 min-w-[200px]">
              <label className="block text-xs font-medium text-gray-400 mb-1.5">
                Stock Ticker
              </label>
              <button
                onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                className="w-full flex items-center justify-between gap-2 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg hover:bg-gray-750 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
              >
                <div className="text-left">
                  <span className="text-white font-semibold">{selectedSymbol}</span>
                  <span className="text-gray-400 text-sm ml-2">
                    {SP500_STOCKS.find(s => s.symbol === selectedSymbol)?.name || ''}
                  </span>
                </div>
                <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`} />
              </button>
              {isDropdownOpen && (
                <>
                  <div
                    className="fixed inset-0 z-10"
                    onClick={() => setIsDropdownOpen(false)}
                  />
                  <div className="absolute z-20 w-full mt-1 bg-gray-800 border border-gray-700 rounded-lg shadow-xl max-h-80 overflow-auto">
                    {/* Group stocks by sector */}
                    {['Technology', 'Energy', 'Healthcare', 'Finance', 'Consumer'].map((sector) => (
                      <div key={sector}>
                        <div className="px-4 py-1.5 bg-gray-900 text-xs font-semibold text-gray-500 uppercase tracking-wider sticky top-0">
                          {sector}
                        </div>
                        {SP500_STOCKS.filter((s: any) => s.sector === sector).map((stock) => (
                          <button
                            key={stock.symbol}
                            onClick={() => {
                              setSelectedSymbol(stock.symbol);
                              setIsDropdownOpen(false);
                            }}
                            className={`w-full px-4 py-2 text-left hover:bg-gray-700 transition-colors ${
                              selectedSymbol === stock.symbol ? 'bg-primary-600/20' : ''
                            }`}
                          >
                            <div className="font-semibold text-white">{stock.symbol}</div>
                            <div className="text-xs text-gray-400">{stock.name}</div>
                          </button>
                        ))}
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>

            {/* Min Relevance */}
            <div className="w-32">
              <label className="block text-xs font-medium text-gray-400 mb-1.5">
                Min Relevance
              </label>
              <input
                type="number"
                min="0"
                max="1"
                step="0.1"
                value={minRelevance}
                onChange={(e) => setMinRelevance(parseFloat(e.target.value))}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
              />
            </div>

            {/* Max Articles */}
            <div className="w-32">
              <label className="block text-xs font-medium text-gray-400 mb-1.5">
                Max Articles
              </label>
              <input
                type="number"
                min="1"
                max="50"
                value={maxArticles}
                onChange={(e) => setMaxArticles(parseInt(e.target.value))}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
              />
            </div>

            {/* Process Button */}
            <button
              onClick={handleProcess}
              disabled={loading}
              className="px-6 py-2 bg-primary-600 hover:bg-primary-500 disabled:bg-primary-600/50 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors flex items-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Newspaper className="w-4 h-4" />
                  Process Pipeline
                </>
              )}
            </button>
          </div>
        </div>
        </div>

        {/* Two Column Layout */}
        <div className="max-w-[1800px] mx-auto flex flex-col lg:flex-row gap-6">
          {/* Left Column - Analysis Results */}
          <div className="flex-1 space-y-6 min-w-0">
            {/* Error Message */}
            {error && (
              <div className="bg-danger-500/10 border border-danger-500/50 rounded-xl p-4 flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-danger-400 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="text-danger-400 font-semibold">Error</h3>
                  <p className="text-danger-300 text-sm">{error}</p>
                </div>
              </div>
            )}

            {/* Loading State */}
            {loading && (
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 flex flex-col items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mb-4"></div>
                <p className="text-gray-400">Processing news pipeline...</p>
              </div>
            )}

            {/* Pipeline Results */}
            {pipelineData && !loading && (
              <div className="space-y-6">
                {/* Final Result - Shown at TOP */}
                {pipelineData.final_result && (
                  <div className="bg-gradient-to-br from-primary-900/50 to-primary-800/30 border border-primary-500/30 rounded-xl p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h2 className="text-xl font-bold text-white flex items-center gap-2">
                        <BarChart3 className="w-6 h-6 text-primary-400" />
                        Sentiment Analysis Result
                      </h2>
                      <div className="text-sm text-gray-400 flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {pipelineData.total_duration_ms}ms
                      </div>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                      {/* Symbol */}
                      <ResultCard label="Symbol" value={pipelineData.final_result.symbol} />

                      {/* Sentiment */}
                      <div className="bg-gray-900/50 rounded-lg p-4">
                        <div className="text-xs text-gray-400 mb-1">Sentiment</div>
                        <div className="flex items-center gap-2">
                          {getSentimentIcon(pipelineData.final_result.sentiment_label)}
                          <div>
                            <div className={`text-lg font-bold ${getSentimentColor(pipelineData.final_result.sentiment_label)}`}>
                              {pipelineData.final_result.aggregated_sentiment.toFixed(3)}
                            </div>
                            <div className={`text-xs font-semibold uppercase ${getSentimentColor(pipelineData.final_result.sentiment_label)}`}>
                              {pipelineData.final_result.sentiment_label}
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Confidence */}
                      <ResultCard
                        label="Confidence"
                        value={`${(pipelineData.final_result.confidence * 100).toFixed(1)}%`}
                      />

                      {/* Impact */}
                      <div className="bg-gray-900/50 rounded-lg p-4">
                        <div className="text-xs text-gray-400 mb-1">Impact</div>
                        <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold border ${getImpactColor(pipelineData.final_result.impact)}`}>
                          {pipelineData.final_result.impact}
                        </span>
                      </div>

                      {/* News Count */}
                      <ResultCard
                        label="News Count"
                        value={pipelineData.final_result.news_count.toString()}
                      />

                      {/* Time Weighted */}
                      <ResultCard
                        label="Time Weighted"
                        value={pipelineData.final_result.time_weighted ? 'Yes' : 'No'}
                      />
                    </div>
                  </div>
                )}

                {/* Pipeline Steps - Below the result */}
                <div>
                  <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
                    Pipeline Execution Details
                  </h3>
                  <div className="space-y-3">
                    {pipelineData.steps.map((step, index) => (
                      <PipelineStepCard
                        key={step.agent}
                        step={step}
                        index={index}
                        icon={getAgentIcon(step.agent)}
                        name={getAgentName(step.agent)}
                      />
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Empty State */}
            {!pipelineData && !loading && !error && (
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 flex flex-col items-center justify-center text-center">
                <Newspaper className="w-16 h-16 text-gray-700 mb-4" />
                <h3 className="text-xl font-semibold text-white mb-2">Ready to Analyze</h3>
                <p className="text-gray-400 max-w-md">
                  Select a stock ticker and click "Process Pipeline" to fetch news, analyze sentiment, and get aggregated results.
                </p>
              </div>
            )}
          </div>

          {/* Right Column - News Feed */}
          <div className="lg:w-[420px] flex-shrink-0">
            <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden sticky top-20">
              <div className="p-4 border-b border-gray-800 flex items-center justify-between">
                <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-2">
                  <FileText className="w-4 h-4" />
                  News Feed
                </h2>
                {articles.length > 0 && (
                  <span className="text-xs text-gray-500">{articles.length} articles</span>
                )}
              </div>
              <div className="max-h-[calc(100vh-200px)] overflow-y-auto">
                {loading && (
                  <div className="p-8 text-center">
                    <Loader2 className="w-8 h-8 animate-spin text-primary-500 mx-auto mb-2" />
                    <p className="text-sm text-gray-400">Fetching news...</p>
                  </div>
                )}
                {!loading && articles.length === 0 && (
                  <div className="p-8 text-center">
                    <Newspaper className="w-12 h-12 text-gray-700 mx-auto mb-2" />
                    <p className="text-sm text-gray-400">
                      {pipelineData ? 'No articles passed the relevance filter' : 'Articles will appear here after processing'}
                    </p>
                  </div>
                )}
                {!loading && articles.length > 0 && (
                  <div className="divide-y divide-gray-800">
                    {articles.map((article, index) => (
                      <ArticleCard key={article.id || index} article={article} />
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

// Pipeline Step Card Component
function PipelineStepCard({
  step,
  index,
  icon,
  name,
}: {
  step: PipelineStep;
  index: number;
  icon: React.ReactNode;
  name: string;
}) {
  const [isExpanded, setIsExpanded] = useState(false);

  const getStatusBadge = () => {
    switch (step.status) {
      case 'completed':
        return (
          <span className="flex items-center gap-1 px-2 py-1 bg-success-500/20 text-success-400 rounded-full text-xs font-semibold">
            <CheckCircle2 className="w-3 h-3" />
            Completed {step.duration_ms && `(${step.duration_ms}ms)`}
          </span>
        );
      case 'processing':
        return (
          <span className="flex items-center gap-1 px-2 py-1 bg-amber-500/20 text-amber-400 rounded-full text-xs font-semibold">
            <Loader2 className="w-3 h-3 animate-spin" />
            Processing
          </span>
        );
      case 'error':
        return (
          <span className="flex items-center gap-1 px-2 py-1 bg-danger-500/20 text-danger-400 rounded-full text-xs font-semibold">
            <AlertCircle className="w-3 h-3" />
            Error
          </span>
        );
    }
  };

  const renderMetrics = () => {
    if (!step.details) return null;

    const details = step.details;

    switch (step.agent) {
      case 'news_fetch_agent':
        return (
          <div className="flex flex-wrap gap-4 mt-3">
            <Metric label="Raw Articles" value={details.raw_articles_count || details.final_articles_count || 0} />
            <Metric label="Final Articles" value={details.final_articles_count || details.final_articles?.length || 0} />
            <Metric label="Sources" value={details.sources_used?.length || 0} />
            <Metric
              label="Data Source"
              value={details.data_source === 'mock' ? '📦 Mock' : '🌐 API'}
              highlight={details.data_source !== 'mock'}
            />
          </div>
        );
      case 'llm_sentiment_agent':
        return (
          <div className="flex flex-wrap gap-4 mt-3">
            <Metric label="Articles Processed" value={details.articles_processed || 0} />
            <Metric label="Cache Hits" value={details.cache_hits || 0} highlight />
            <Metric label="Cache Misses" value={details.cache_misses || 0} />
            {details.cache_hit_rate !== undefined && (
              <Metric label="Hit Rate" value={`${(details.cache_hit_rate * 100).toFixed(1)}%`} />
            )}
          </div>
        );
      case 'sentiment_aggregator':
        return (
          <div className="flex flex-wrap gap-4 mt-3">
            <Metric label="News Count" value={details.news_count || 0} />
            <Metric label="Sentiment" value={details.aggregated_sentiment?.toFixed(3) || 'N/A'} />
            <Metric label="Confidence" value={details.confidence?.toFixed(2) || 'N/A'} />
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
      <div className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary-500/20 flex items-center justify-center text-primary-400">
              {icon}
            </div>
            <div>
              <div className="text-white font-semibold">
                Step {index + 1}: {name}
              </div>
            </div>
          </div>
          {getStatusBadge()}
        </div>

        {renderMetrics()}

        {step.error && (
          <div className="mt-3 p-3 bg-danger-500/10 border border-danger-500/30 rounded-lg">
            <p className="text-danger-400 text-sm">{step.error}</p>
          </div>
        )}
      </div>

      {/* Expandable Details */}
      {step.details && (
        <div className="border-t border-gray-800">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="w-full px-4 py-2 text-sm text-gray-400 hover:text-white hover:bg-gray-800/50 transition-colors flex items-center gap-2"
          >
            <ChevronDown className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
            {isExpanded ? 'Hide Details' : 'View Details'}
          </button>
          {isExpanded && (
            <div className="px-4 pb-4">
              <pre className="bg-gray-950 border border-gray-800 rounded-lg p-3 text-xs text-gray-300 overflow-auto max-h-64">
                {JSON.stringify(step.details, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Metric Component
function Metric({ label, value, highlight = false }: { label: string; value: string | number; highlight?: boolean }) {
  return (
    <div className="flex flex-col">
      <span className="text-xs text-gray-500">{label}</span>
      <span className={`text-sm font-semibold ${highlight ? 'text-primary-400' : 'text-white'}`}>
        {value}
      </span>
    </div>
  );
}

// Result Card Component
function ResultCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-gray-900/50 rounded-lg p-4">
      <div className="text-xs text-gray-400 mb-1">{label}</div>
      <div className="text-lg font-bold text-white">{value}</div>
    </div>
  );
}

// Article Card Component
function ArticleCard({ article }: { article: Article }) {
  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  const getRelevanceColor = (score?: number) => {
    if (!score) return 'text-gray-400';
    if (score >= 0.7) return 'text-success-400';
    if (score >= 0.4) return 'text-amber-400';
    return 'text-gray-400';
  };

  return (
    <div className="p-4 hover:bg-gray-800/50 transition-colors">
      {/* Title */}
      <h4 className="text-sm font-semibold text-white mb-2 line-clamp-2 leading-snug">
        {article.title}
      </h4>

      {/* Meta Info */}
      <div className="flex items-center gap-2 text-xs text-gray-400 mb-2">
        <span className="font-medium text-primary-400">{article.source}</span>
        <span>•</span>
        <span>{formatDate(article.published_at)}</span>
        {article.relevance_score !== undefined && (
          <>
            <span>•</span>
            <span className={`font-semibold ${getRelevanceColor(article.relevance_score)}`}>
              {(article.relevance_score * 100).toFixed(0)}% relevant
            </span>
          </>
        )}
      </div>

      {/* Summary */}
      {article.summary && (
        <p className="text-xs text-gray-400 mb-3 line-clamp-3 leading-relaxed">
          {article.summary}
        </p>
      )}

      {/* URL Link */}
      {article.url && (
        <a
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-xs text-primary-400 hover:text-primary-300 transition-colors"
        >
          <ExternalLink className="w-3 h-3" />
          Read full article
        </a>
      )}
    </div>
  );
}

