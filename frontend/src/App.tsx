import { Link, NavLink, Navigate, Route, Routes } from 'react-router'
import { Explore } from './Explore'
import { DestinationDetails } from './DestinationDetails'
import { MyTrips } from './MyTrips'
import { TripBuilder } from './TripBuilder'
import { DraftProvider } from './trips/DraftContext'
import { useLocation } from 'react-router'

export function BrandMark() {
  return <svg viewBox="0 0 40 40" fill="none" aria-hidden="true"><path d="M20 5 8 24h8L10 33h20l-6-9h8L20 5Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" /><path d="M20 27v10" stroke="currentColor" strokeWidth="1.6" /></svg>
}
export function App() {
  const preview = import.meta.env.DEV && new URLSearchParams(useLocation().search).get('preview') === '1'
  return <DraftProvider><div className="app-shell">
    <a className="skip-link" href="#main">Skip to content</a>
    <header className="site-header">
      <Link to="/explore" className="brand" aria-label="Pathways home"><BrandMark /><span>pathways<span className="brand-dot">.</span></span></Link>
      <nav aria-label="Main navigation"><NavLink to={`/explore${preview ? '?preview=1' : ''}`}>Explore</NavLink><NavLink to={`/trips/new${preview ? '?preview=1' : ''}`}>Day trips</NavLink><NavLink end to={`/trips${preview ? '?preview=1' : ''}`}>My Trips</NavLink></nav>
      <span className="header-note"><span className="tiny-sun">✳</span> A little closer to nature</span>
    </header>
    <Routes>
      <Route path="/explore" element={<Explore />} />
      <Route path="/destinations/:slug" element={<DestinationDetails />} />
      <Route path="/trips" element={<MyTrips />} /><Route path="/trips/new" element={<TripBuilder />} />
      <Route path="/" element={<Navigate to="/explore" replace />} />
      <Route path="*" element={<main id="main" className="not-found"><h1>A path less traveled.</h1><p>This page could not be found.</p><Link to="/explore" className="primary-button">Back to Explore</Link></main>} />
    </Routes>
    <footer className="site-footer"><span>Made for wandering. Rooted in Georgia.</span><span>Take only memories. Leave only footprints.</span></footer>
  </div></DraftProvider>
}


