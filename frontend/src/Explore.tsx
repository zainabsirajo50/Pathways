import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router'
import { useQuery } from '@tanstack/react-query'
import { loadCategories, loadDestinations } from './catalog/data'
import { PAGE_SIZE, categories, label, type Category, type CatalogMode } from './catalog/types'
import { DestinationCard } from './components/DestinationCard'
import { MapPanel } from './components/MapPanel'

export function Explore() {
  const [params, setParams] = useSearchParams()
  const [mode, setMode] = useState<CatalogMode>(() => import.meta.env.DEV && (params.get('preview') ?? new URLSearchParams(window.location.search).get('preview')) === '1' ? 'fixtures' : 'public')
  const [input, setInput] = useState(params.get('q')?.slice(0, 160) || '')
  const [q, setQ] = useState(params.get('q')?.slice(0, 160) || '')
  const [category, setCategory] = useState<Category | ''>(categories.includes(params.get('category') as Category) ? params.get('category') as Category : '')
  const [page, setPage] = useState(Math.min(1_000_000, Math.max(1, Math.trunc(Number(params.get('page'))) || 1)))
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null)
  useEffect(() => {
    const next = new URLSearchParams()
    if (q) next.set('q', q)
    if (category) next.set('category', category)
    if (page > 1) next.set('page', String(page))
    if (import.meta.env.DEV && mode === 'fixtures') next.set('preview', '1')
    setParams(next, { replace: true })
  }, [q, category, page, mode, setParams])
  const filters = { q, category, page }
  const catalog = useQuery({ queryKey: ['destinations', mode, filters], queryFn: ({ signal }) => loadDestinations(mode, filters, signal) })
  const taxonomy = useQuery({ queryKey: ['categories', mode], queryFn: ({ signal }) => loadCategories(mode, signal) })
  const selected = catalog.data?.items.find(item => item.slug === selectedSlug)
  const fixtures = mode === 'fixtures'
  const resetSelection = () => { setPage(1); setSelectedSlug(null) }
  function clearFilters() { setInput(''); setQ(''); setCategory(''); resetSelection() }
  function changeMode() { setMode(fixtures ? 'public' : 'fixtures'); clearFilters() }

  return <main id="main">
    <section className="intro"><div><p className="eyebrow">OUTSIDE IS CLOSER THAN YOU THINK</p><h1>Find your kind of <em>away.</em></h1><p className="intro-copy">Waterfalls, winding trails, quiet shores. Discover a little more of Georgia.</p></div><span className="intro-stamp" aria-hidden="true">GEORGIA<br/><span>↟</span><br/>OUT IN THE OPEN</span></section>
    {import.meta.env.DEV && <div className={`dev-banner ${fixtures ? 'fixture-active' : ''}`}>
      <div><strong>{fixtures ? 'Development preview · fixture data' : 'Development · public catalog'}</strong><span>{fixtures ? 'Sample content only. Destinations are not verified or route-ready. No database data is changed.' : 'Only approved destinations appear here. Preview fixtures are available separately.'}</span></div>
      <button className="text-button" onClick={changeMode}>{fixtures ? 'Use public API' : 'Preview fixtures'} ↗</button>
    </div>}
    <div className="explore-grid">
      <section className="catalog-panel" aria-label="Explore destinations">
        <form className="search-form" onSubmit={event => { event.preventDefault(); setQ(input.trim()); resetSelection() }}>
          <span aria-hidden="true" className="search-icon">⌕</span><label className="sr-only" htmlFor="destination-search">Search destination names</label>
          <input id="destination-search" type="search" placeholder="Where would you like to wander?" value={input} maxLength={160} onChange={event => setInput(event.target.value)} />
          <button type="submit">Search <span aria-hidden="true">→</span></button>
        </form>
        <div className="category-filters" role="group" aria-label="Filter by category"><button aria-pressed={category === ''} onClick={() => { setCategory(''); resetSelection() }}>All places</button>
          {taxonomy.data?.map(item => <button key={item} aria-pressed={category === item} onClick={() => { setCategory(item); resetSelection() }}>{label(item)}</button>)}
        </div>
        {taxonomy.isError && <p role="alert" className="category-error">Category filters could not be loaded. <button className="text-button" onClick={() => void taxonomy.refetch()}>Retry filters</button></p>}
        <div className="results-heading"><h2>{q || category ? 'Your discoveries' : 'Places to pause'}</h2><span aria-live="polite">{catalog.isPending ? 'Finding places…' : catalog.isError ? 'Catalog unavailable' : `${catalog.data.total} ${fixtures ? 'preview ' : ''}${catalog.data.total === 1 ? 'place' : 'places'}`}</span></div>
        <div className="destination-list" role="region" aria-label="Destination results" tabIndex={0}>
        {catalog.isPending ? <div className="cards-grid" role="status" aria-label="Loading destinations">{[1, 2, 3, 4].map(i => <div key={i} className="skeleton-card"><div/><span/><span/></div>)}<span className="sr-only">Loading destinations</span></div>
          : catalog.isError ? <div className="catalog-state" role="alert"><span className="state-icon" aria-hidden="true">↻</span><h3>A small detour.</h3><p>{catalog.error instanceof Error ? catalog.error.message : 'We could not reach the catalog.'}</p><button className="primary-button" onClick={() => void catalog.refetch()}>Try again</button></div>
          : catalog.data.items.length === 0 ? <div className="catalog-state"><span className="state-icon" aria-hidden="true">↟</span><h3>{q || category ? 'No places on this path.' : 'Good places take a little care.'}</h3><p>{q || category ? 'Try another name or category to find your next escape.' : 'Our Georgia catalog is being carefully reviewed. Destinations will appear here when they are ready to share.'}</p>{(q || category || page > 1) && <button className="primary-button" onClick={clearFilters}>Clear filters</button>}</div>
          : <div className="cards-grid">{catalog.data.items.map(destination => <DestinationCard key={destination.slug} destination={destination} selected={selectedSlug === destination.slug} onSelect={() => setSelectedSlug(destination.slug)}/>)}</div>}
        </div>
        {catalog.data && catalog.data.total > PAGE_SIZE && !catalog.isError && <nav className="pagination" aria-label="Destination pages"><button disabled={page === 1} onClick={() => { setPage(page - 1); setSelectedSlug(null) }}>← Previous</button><span>Page {page} of {Math.ceil(catalog.data.total / PAGE_SIZE)}</span><button disabled={page * PAGE_SIZE >= catalog.data.total} onClick={() => { setPage(page + 1); setSelectedSlug(null) }}>Next →</button></nav>}
        <p className="catalog-footnote">A little fresh air goes a long way. <span aria-hidden="true">✳</span></p>
      </section>
      <MapPanel destinations={catalog.data?.items ?? []} loading={catalog.isFetching} onSelect={slug => { setSelectedSlug(slug); document.getElementById(`card-${slug}`)?.scrollIntoView({ block: 'nearest', inline: 'nearest' }) }} selected={selected} fixtures={fixtures} onClear={() => setSelectedSlug(null)}/>
    </div>
  </main>
}




