import { NavLink, Outlet } from 'react-router-dom'

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  isActive ? 'text-sm font-medium text-slate-900' : 'text-sm text-slate-500 hover:text-slate-900'

/** Application shell: header with primary navigation + routed content. */
export function Layout() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="flex items-center gap-6 border-b border-slate-200 bg-white px-6 py-4">
        <h1 className="text-lg font-semibold">AI SAST Platform</h1>
        <nav className="flex items-center gap-4">
          <NavLink to="/" end className={navLinkClass}>
            Upload
          </NavLink>
          {/* The scans history view arrives in a later slice. */}
          <span className="cursor-not-allowed text-sm text-slate-300" aria-disabled="true">
            Scans
          </span>
        </nav>
      </header>
      <main className="p-6">
        <Outlet />
      </main>
    </div>
  )
}
