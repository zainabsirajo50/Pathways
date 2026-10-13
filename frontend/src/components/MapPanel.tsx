import { Link, useLocation } from 'react-router'
import { DestinationMap } from './DestinationMap'
import { label, type Destination } from '../catalog/types'

export function MapPanel({ selected, fixtures, onClear, destinations, onSelect, loading }: { selected?: Destination; fixtures: boolean; onClear: () => void; destinations: Destination[]; onSelect: (slug: string) => void; loading: boolean }) {
  const { search } = useLocation()
  return <aside className="map-panel" aria-label="Map and selected destination">
    <DestinationMap destinations={destinations} selected={selected} onSelect={onSelect} fixtures={fixtures} loading={loading}/>
    <section className="selection-panel" aria-label="Destination details" aria-live="polite">
      {selected ? <><div className="selection-heading"><span className="eyebrow">{fixtures ? 'Preview destination' : 'Selected destination'}</span><button className="text-button" onClick={onClear} aria-label="Clear selected destination">Close ×</button></div>
        <h3>{selected.name}</h3><p className="selection-location">{label(selected.category)} · {selected.city || selected.region}, {selected.state}</p>
        <p className="preview-description">{selected.description || 'A description is not yet available.'}</p>
        {fixtures && selected.access_notes && <p className="fixture-coordinate-label">Official published entrance reference · routing untested</p>}
        <Link className="preview-details" to={`/destinations/${encodeURIComponent(selected.slug)}${search}`}>View Details <span aria-hidden="true">↗</span></Link>
      </> : <><span className="eyebrow">Your next little escape</span><h3>Start with a place.</h3><p>Select a destination to see more about it here.</p><span className="selection-hint">No routes have been tested in this preview.</span></>}
    </section>
  </aside>
}



