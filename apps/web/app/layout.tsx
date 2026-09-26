import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Shopilot — Your AI Shopping Agent',
  description: "Tell us what you're looking for. Shopilot finds, compares and tracks it.",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="min-h-screen flex flex-col bg-slate-50 text-slate-900 antialiased">
        <header className="border-b border-slate-200 bg-white/80 backdrop-blur-md sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <a href="/" className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold text-lg">
                S
              </div>
              <span className="font-bold text-xl tracking-tight text-slate-900">
                Shopilot
              </span>
            </a>
            <nav className="flex items-center space-x-6 text-sm font-medium text-slate-600">
              <a href="/deals" className="hover:text-slate-900 transition-colors">Deals</a>
              <a href="/price-watch" className="hover:text-slate-900 transition-colors">Price Watch</a>
              <a href="/compare" className="hover:text-slate-900 transition-colors">Compare</a>
              <a href="/login" className="bg-slate-900 text-white px-4 py-2 rounded-lg hover:bg-slate-800 transition-colors">Sign In</a>
            </nav>
          </div>
        </header>

        <main className="flex-1">
          {children}
        </main>

        <footer className="border-t border-slate-200 bg-white py-8">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-xs text-slate-500 space-y-2">
            <p>Shopilot may earn a commission when you purchase through some links. This does not increase the price you pay.</p>
            <p>© {new Date().getFullYear()} Shopilot. All rights reserved.</p>
            <div className="flex justify-center space-x-4 pt-2">
              <a href="/privacy" className="hover:underline">Privacy Policy</a>
              <a href="/terms" className="hover:underline">Terms of Service</a>
              <a href="/affiliate-disclosure" className="hover:underline">Affiliate Disclosure</a>
            </div>
          </div>
        </footer>
      </body>
    </html>
  )
}
