import { useState } from 'react'
import Sidebar from './Sidebar'

export default function AppShell({
  activeView,
  onNavigate,
  flaggedCount,
  children,
}) {
  const [mobileOpen, setMobileOpen] = useState(false)

  const navigate = (view) => {
    onNavigate(view)
    setMobileOpen(false)
  }

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar
        activeView={activeView}
        onNavigate={navigate}
        flaggedCount={flaggedCount}
        mobileOpen={mobileOpen}
        onClose={() => setMobileOpen(false)}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-14 items-center gap-4 border-b border-slate-200 bg-white/90 px-4 backdrop-blur sm:px-6 lg:hidden">
          <button
            type="button"
            onClick={() => setMobileOpen(true)}
            className="rounded-lg p-2 text-slate-600 hover:bg-slate-100"
            aria-label="Open menu"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <span className="text-sm font-semibold text-slate-900">Breathe ESG</span>
        </header>

        <main className="flex-1 p-4 sm:p-6 lg:p-8">{children}</main>
      </div>
    </div>
  )
}
