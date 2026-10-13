import { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router'
import { useDraft } from './trips/DraftContext'
import { DestinationMap, hasCoordinates } from './components/DestinationMap'
import { label } from './catalog/types'
import { Availability } from './trips/Availability'
import { DurationInput } from './trips/DurationInput'

export function TripBuilder() {
  useEffect(() => { document.title = 'Day Trip Builder · Pathways'; return () => { document.title = 'Explore Georgia · Pathways' } }, [])
  const { search } = useLocation()
  const preview = import.meta.env.DEV && new URLSearchParams(search).get('preview') === '1'
  const { draft, update, save, dirty, activeId, error, reset } = useDraft(preview ? 'fixtures' : 'public')
  const [message, setMessage] = useState('')
  useEffect(() => { setMessage('') }, [draft])
  const [selected, setSelected] = useState<string | null>(null)
  const destinations = draft.stops.map(stop => stop.destination)
  const total = draft.stops.reduce((sum, stop) => sum + stop.minutes, 0)
  function move(index: number, offset: number) {
    update(current => {
      const stops = [...current.stops]
      if (index + offset < 0 || index + offset >= stops.length) return current
      ;[stops[index], stops[index + offset]] = [stops[index + offset], stops[index]]
      return { ...current, stops }
    })
  }
  return <main id="main" className="trip-page">
    <section className="intro"><div><p className="eyebrow">A DAY MADE YOUR WAY</p><h1>A little plan. <em>A little escape.</em></h1><p className="intro-copy">Gather your places and leave room to wander.</p></div></section>
    <div className={`dev-banner ${preview ? 'fixture-active' : ''}`}><div><strong>{preview ? 'Development preview trip · fixture stops only' : 'Browser trip draft'}</strong><span>Draft retained in this browser only. No account sync. No routes or travel times are calculated.</span></div></div>
    <p role="status">{dirty ? activeId ? 'Unsaved changes to saved trip' : 'Unsaved draft' : 'Saved trip'}{message && ` · ${message}`}</p>{error && <div role="alert">{error}<button onClick={() => { if (window.confirm('Reset all browser trips in this mode?')) reset() }}>Reset browser trips</button></div>}<div className="stop-actions"><button className="primary-button" disabled={!draft.name.trim()} onClick={() => setMessage(save() ? 'Trip saved in this browser.' : 'Trip could not be saved.')}>Save Trip</button><Link to={`/trips${preview ? '?preview=1' : ''}`}>My Trips →</Link></div><div className="trip-grid"><section className="trip-editor" aria-label="Trip draft">
      <div className="trip-fields"><label>Trip name<input maxLength={120} placeholder="A day in the Georgia outdoors" value={draft.name} onChange={event => update(current => ({ ...current, name: event.target.value }))}/></label><label>Trip date (optional)<input type="date" value={draft.date} onChange={event => update(current => ({ ...current, date: event.target.value }))}/></label></div>
      <div className="trip-summary" aria-live="polite"><strong>{draft.stops.length} {draft.stops.length === 1 ? 'stop' : 'stops'}</strong><span>{total} minutes planned visiting · excludes travel</span></div>
      {draft.stops.length === 0 ? <div className="catalog-state"><h2>Start with a place.</h2><p>Add a destination from Explore or its details page to begin your day trip.</p></div> : <ol className="trip-stops">{draft.stops.map((stop, index) => <li key={stop.destination.slug} className={selected === stop.destination.slug ? 'stop-selected' : ''}>
        <div className="stop-title"><span className="stop-number">{index + 1}</span><div><Link to={`/destinations/${encodeURIComponent(stop.destination.slug)}${preview ? '?preview=1' : ''}`}>{stop.destination.name}</Link><p>{label(stop.destination.category)} · {stop.destination.city || stop.destination.region}</p></div></div>
        <p className="stop-coordinate-status">{hasCoordinates(stop.destination) ? preview ? 'Mapped reference · routing untested' : 'Mapped display point · no route verification' : 'Not mapped · coordinates unavailable'}</p>
        <Availability slug={stop.destination.slug} mode={preview ? 'fixtures' : 'public'}/><DurationInput name={stop.destination.name} minutes={stop.minutes} onChange={value => update(current => ({ ...current, stops: current.stops.map(item => item.destination.slug === stop.destination.slug ? { ...item, minutes: value } : item) }))}/>
        <div className="stop-actions"><button disabled={index === 0} aria-label={`Move ${stop.destination.name} up`} onClick={() => move(index, -1)}>↑ Up</button><button disabled={index === draft.stops.length - 1} aria-label={`Move ${stop.destination.name} down`} onClick={() => move(index, 1)}>↓ Down</button><button aria-label={`Remove ${stop.destination.name}`} onClick={() => { update(current => ({ ...current, stops: current.stops.filter(item => item.destination.slug !== stop.destination.slug) })); if (selected === stop.destination.slug) setSelected(null) }}>Remove</button></div>
      </li>)}</ol>}
      <Link className="primary-button" to={`/explore${preview ? '?preview=1' : ''}`}>Find more places ↗</Link>
    </section><aside className="trip-map" aria-label="Ordered trip stop map"><DestinationMap destinations={destinations} selected={destinations.find(row => row.slug === selected)} onSelect={setSelected} fixtures={preview} loading={false} numbered/><p className="trip-map-note">Numbers match your stop order. Missing-coordinate stops have no marker. No route lines or travel estimates.</p></aside></div>
  </main>
}



