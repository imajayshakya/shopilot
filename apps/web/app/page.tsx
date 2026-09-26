'use client'

import { useState } from 'react'
import { Search, Sparkles, ShoppingBag, ShieldCheck, ArrowRight, Star, ExternalLink, CheckCircle2 } from 'lucide-react'

interface Offer {
  merchant: string
  merchant_slug: string
  price: number
  mrp?: number
  currency: string
  discount_percentage?: number
  availability: string
  rating?: number
  review_count?: number
  product_url: string
  affiliate_url?: string
}

interface Recommendation {
  rank: number
  match_percentage: number
  why_this_pick: string[]
  strengths: string[]
  best_offer?: Offer
  product: {
    canonical_id: string
    title: string
    brand?: string
    model?: string
    image_url?: string
    specifications: Record<string, any>
  }
}

interface SearchResponse {
  search_id: string
  query: string
  recommendations: Recommendation[]
  pipeline_stats: {
    providers_searched: string[]
    total_provider_results: number
  }
}

const POPULAR_SEARCHES = [
  'Phone under ₹40,000 with good camera',
  'Laptop under ₹70,000 for coding',
  'Wireless ANC headphones under ₹10,000',
  '4K Smart TV under ₹50,000',
]

export default function HomePage() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [loadingStage, setLoadingStage] = useState('')
  const [results, setResults] = useState<SearchResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) return

    setQuery(searchQuery)
    setLoading(true)
    setError(null)
    setResults(null)

    // Progressive loading states
    setLoadingStage('Understanding your request...')
    setTimeout(() => setLoadingStage('Searching merchant stores...'), 600)
    setTimeout(() => setLoadingStage('Comparing offers & normalizing...'), 1200)
    setTimeout(() => setLoadingStage('Finding the best matches...'), 1800)

    try {
      const res = await fetch('http://localhost:8000/api/v1/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery }),
      })

      if (!res.ok) {
        throw new Error('Search request failed')
      }

      const data: SearchResponse = await res.json()
      setResults(data)
    } catch (err: any) {
      setError('Failed to fetch search results. Make sure the backend API is running on localhost:8000.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-12">
      {/* Hero Section */}
      <div className="text-center max-w-3xl mx-auto space-y-4">
        <div className="inline-flex items-center space-x-2 bg-blue-50 text-blue-700 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider">
          <Sparkles className="w-3.5 h-3.5" />
          <span>AI Shopping Agent</span>
        </div>
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-slate-900">
          Your AI Shopping Agent
        </h1>
        <p className="text-lg text-slate-600">
          Tell us what you're looking for. Shopilot finds, compares, and tracks it across supported stores.
        </p>
      </div>

      {/* Main Search Input */}
      <div className="max-w-2xl mx-auto">
        <form
          onSubmit={(e) => {
            e.preventDefault()
            handleSearch(query)
          }}
          className="relative flex items-center"
        >
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="What are you looking for? (e.g. phone under ₹40,000 with a good camera)"
            className="w-full pl-5 pr-36 py-4 rounded-2xl border border-slate-300 bg-white text-slate-900 placeholder-slate-400 text-base shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent transition-all"
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="absolute right-2 bg-blue-600 hover:bg-blue-700 text-white font-medium px-5 py-2.5 rounded-xl flex items-center space-x-2 shadow transition-all disabled:opacity-50"
          >
            <Search className="w-4 h-4" />
            <span>{loading ? 'Searching...' : 'Find the best'}</span>
          </button>
        </form>

        {/* Popular searches */}
        <div className="mt-4 flex flex-wrap gap-2 items-center justify-center text-xs text-slate-500">
          <span className="font-semibold text-slate-700">Try:</span>
          {POPULAR_SEARCHES.map((s, idx) => (
            <button
              key={idx}
              onClick={() => handleSearch(s)}
              className="bg-slate-200/60 hover:bg-slate-200 text-slate-700 px-2.5 py-1 rounded-lg transition-colors"
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="max-w-xl mx-auto text-center py-12 space-y-4">
          <div className="inline-block w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-sm font-medium text-slate-600 animate-pulse">{loadingStage}</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="max-w-2xl mx-auto p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm text-center">
          {error}
        </div>
      )}

      {/* Results Section */}
      {results && (
        <div className="space-y-6">
          <div className="flex justify-between items-center border-b border-slate-200 pb-4">
            <div>
              <h2 className="text-2xl font-bold text-slate-900">Recommended Picks</h2>
              <p className="text-xs text-slate-500 mt-1">
                Searched across {results.pipeline_stats.providers_searched.join(', ')} • {results.recommendations.length} top matches found
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {results.recommendations.map((rec) => (
              <div
                key={rec.product.canonical_id}
                className="bg-white rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow flex flex-col overflow-hidden"
              >
                {/* Header Badge */}
                <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
                  <span className="inline-flex items-center space-x-1 text-xs font-semibold text-blue-700 bg-blue-100/70 px-2.5 py-1 rounded-full">
                    <span>Rank #{rec.rank}</span>
                    <span>•</span>
                    <span>{rec.match_percentage}% Match</span>
                  </span>
                  {rec.best_offer?.merchant && (
                    <span className="text-xs text-slate-500 font-medium">
                      at {rec.best_offer.merchant}
                    </span>
                  )}
                </div>

                {/* Content */}
                <div className="p-5 flex-1 flex flex-col space-y-4">
                  <div>
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                      {rec.product.brand}
                    </span>
                    <h3 className="font-bold text-slate-900 text-base line-clamp-2 mt-0.5">
                      {rec.product.title}
                    </h3>
                  </div>

                  {/* Price */}
                  {rec.best_offer && (
                    <div className="flex items-baseline space-x-2">
                      <span className="text-2xl font-extrabold text-slate-900">
                        ₹{rec.best_offer.price.toLocaleString('en-IN')}
                      </span>
                      {rec.best_offer.mrp && rec.best_offer.mrp > rec.best_offer.price && (
                        <span className="text-sm text-slate-400 line-through">
                          ₹{rec.best_offer.mrp.toLocaleString('en-IN')}
                        </span>
                      )}
                      {rec.best_offer.discount_percentage && (
                        <span className="text-xs font-bold text-green-600 bg-green-50 px-2 py-0.5 rounded">
                          {rec.best_offer.discount_percentage}% off
                        </span>
                      )}
                    </div>
                  )}

                  {/* Rating */}
                  {rec.best_offer?.rating && (
                    <div className="flex items-center space-x-1.5 text-xs text-slate-600">
                      <Star className="w-4 h-4 fill-amber-400 text-amber-400" />
                      <span className="font-bold">{rec.best_offer.rating}</span>
                      <span>({rec.best_offer.review_count?.toLocaleString('en-IN')} reviews)</span>
                    </div>
                  )}

                  {/* Why this pick bullet points */}
                  <div className="space-y-1.5 pt-2 border-t border-slate-100 text-xs">
                    <span className="font-semibold text-slate-700 block mb-1">Why this pick:</span>
                    {rec.why_this_pick.slice(0, 4).map((bullet, idx) => (
                      <div key={idx} className="flex items-start space-x-1.5 text-slate-600">
                        <CheckCircle2 className="w-3.5 h-3.5 text-green-600 shrink-0 mt-0.5" />
                        <span>{bullet.replace(/^✓\s*/, '')}</span>
                      </div>
                    ))}
                  </div>

                  {/* CTA Buttons */}
                  <div className="pt-4 mt-auto flex items-center space-x-2">
                    {rec.best_offer?.product_url && (
                      <a
                        href={rec.best_offer.product_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium text-xs py-2.5 rounded-xl flex items-center justify-center space-x-1.5 transition-colors"
                      >
                        <span>Buy at {rec.best_offer.merchant}</span>
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* How it Works Section */}
      {!results && !loading && (
        <div className="border-t border-slate-200 pt-12 space-y-8">
          <h2 className="text-2xl font-bold text-center text-slate-900">How Shopilot Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 text-center">
            <div className="bg-white p-6 rounded-2xl border border-slate-200 space-y-2">
              <div className="w-10 h-10 bg-blue-50 text-blue-600 rounded-xl flex items-center justify-center mx-auto font-bold">1</div>
              <h3 className="font-bold text-slate-900">Describe Intent</h3>
              <p className="text-xs text-slate-500">Tell us what you want in plain text with budget or specs.</p>
            </div>
            <div className="bg-white p-6 rounded-2xl border border-slate-200 space-y-2">
              <div className="w-10 h-10 bg-blue-50 text-blue-600 rounded-xl flex items-center justify-center mx-auto font-bold">2</div>
              <h3 className="font-bold text-slate-900">Multi-Store Search</h3>
              <p className="text-xs text-slate-500">We search Amazon, Flipkart, Croma and more concurrently.</p>
            </div>
            <div className="bg-white p-6 rounded-2xl border border-slate-200 space-y-2">
              <div className="w-10 h-10 bg-blue-50 text-blue-600 rounded-xl flex items-center justify-center mx-auto font-bold">3</div>
              <h3 className="font-bold text-slate-900">Compare & Score</h3>
              <p className="text-xs text-slate-500">We match products across stores and rank them objectively.</p>
            </div>
            <div className="bg-white p-6 rounded-2xl border border-slate-200 space-y-2">
              <div className="w-10 h-10 bg-blue-50 text-blue-600 rounded-xl flex items-center justify-center mx-auto font-bold">4</div>
              <h3 className="font-bold text-slate-900">Buy with Confidence</h3>
              <p className="text-xs text-slate-500">See transparent reasoning and purchase directly from merchants.</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
