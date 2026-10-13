import { useEffect, useRef } from 'react'
import { Link, useLocation, useParams } from 'react-router'
import { useQuery } from '@tanstack/react-query'
import { ApiError } from './catalog/api'
import { loadDestination } from './catalog/data'
import { label } from './catalog/types'
import { Landscape } from './components/Landscape'
import { DestinationMap, hasCoordinates } from './components/DestinationMap'
import { AddToTrip } from './trips/AddToTrip'

export function DestinationDetails() {
  const { slug = '' } = useParams()
  const { search } = useLocation()
  const fixtures = import.meta.env.DEV && new URLSearchParams(search).get('preview') === '1'
  const mode = fixtures ? 'fixtures' : 'public'
  const destination = useQuery({ queryKey: ['destination', mode, slug],
    queryFn: ({ signal }) => loadDestination(mode, slug, signal),
    retry: (count, error) => !(error instanceof ApiError && error.status === 404) && count < 1 })
  const heading = useRef<HTMLHeadingElement>(null)
  useEffect(() => { heading.current?.focus() }, [slug, destination.isPending])
  const row = destination.data
  useEffect(() => {
    document.title = row ? `${row.name} · Pathways` : 'Destination · Pathways'
    return () => { document.title = 'Explore Georgia · Pathways' }
  }, [row?.name])
  const website = row?.official_website && /^https?:\/\//i.test(row.official_website) ? row.official_website : null
  return <main id="main" className="details-page">
    <Link className="back-link" to={`/explore${search}`}>← Back to Explore</Link>
    {fixtures && <div className="dev-banner fixture-active"><div><strong>Development preview · fixture data</strong><span>Sample content only. Not verified or route-ready. No database data is changed.</span></div></div>}
    {destination.isPending ? <div className="catalog-state" role="status">Loading destination…</div>
      : destination.isError ? <section className="catalog-state" role="alert"><h1 ref={heading} tabIndex={-1}>{destination.error instanceof ApiError && destination.error.status === 404 ? 'This place is not available.' : 'A small detour.'}</h1><p>{destination.error instanceof ApiError && destination.error.status === 404 ? 'This destination could not be found in the available catalog.' : 'The destination could not be loaded. Please try again.'}</p>{!(destination.error instanceof ApiError && destination.error.status === 404) && <button className="primary-button" onClick={() => void destination.refetch()}>Try again</button>}</section>
      : row && <>
        <header className="details-header"><p className="eyebrow">{label(row.category)} · {row.city || row.region}, {row.state}</p><h1 ref={heading} tabIndex={-1}>{row.name}</h1><p>A little closer to your next escape.</p></header>
        <div className="details-grid">
          <section aria-label="About this destination"><div className="details-art"><Landscape category={row.category}/><span className="art-label">Illustration · destination photography unavailable</span></div>
            <div className="details-copy"><h2>A sense of place</h2><p>{row.description || 'A description is not yet available for this destination.'}</p>
              <h2>Before you go</h2><p>{row.access_notes || 'Visitor access information is not yet available. Check official visitor information before setting out.'}</p>
              {website ? <a className="official-link" href={website} target="_blank" rel="noopener noreferrer">Official visitor information ↗</a> : <p className="details-muted">An official website is not available in this catalog record.</p>}
            </div>
          </section>
          <aside className="details-sidebar"><section className="details-location" aria-label="Destination location"><h2>Find your bearings</h2>
            {hasCoordinates(row) ? <><div className="details-map"><DestinationMap destinations={[row]} selected={row} onSelect={() => {}} fixtures={fixtures} loading={false}/></div><p className="coordinate-note">{fixtures ? 'Published entrance reference in development preview only. Routing remains untested.' : 'Catalog display location only. This marker is not a verified driving route or arrival entrance.'}</p></> : <div className="details-no-location"><span aria-hidden="true">↟</span><p>Location coordinates are not available. This destination remains available to explore.</p></div>}
          </section><section className="details-trip"><p className="eyebrow">Make room for outside</p><h2>Your next little escape.</h2><p>Gather your places in a day-trip draft.</p><AddToTrip destination={row}/><p className="details-muted">Trips stay in this browser only. No account sync or route calculations.</p></section></aside>
        </div>
      </>}
  </main>
}


