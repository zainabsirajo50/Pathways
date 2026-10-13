import { Link, useLocation } from 'react-router'
import type { Destination } from '../catalog/types'
import { label } from '../catalog/types'
import { Landscape } from './Landscape'
import { AddToTrip } from '../trips/AddToTrip'

export function DestinationCard({ destination, selected, onSelect }: { destination: Destination; selected: boolean; onSelect: () => void }) {
  const { search } = useLocation()
  return <article id={`card-${destination.slug}`} className={`destination-card ${selected ? 'is-selected' : ''}`}>
    <div className="card-art"><Landscape category={destination.category}/><span className="category-tag">{label(destination.category)}</span><span className="art-label">Illustration</span></div>
    <div className="card-content"><p className="eyebrow location">{destination.city || destination.region}, {destination.state}</p>
      <h3><Link className="card-title-link" to={`/destinations/${encodeURIComponent(destination.slug)}${search}`}>{destination.name}</Link></h3><p className="card-description">{destination.description || 'Discover this destination and its outdoor surroundings.'}</p>
      <button type="button" className="card-select" aria-pressed={selected} onClick={onSelect} aria-label={`Explore ${destination.name}`}>
        {selected ? 'Selected destination' : 'Take a closer look'}<span aria-hidden="true">{selected ? '✓' : '↗'}</span>
      </button>
      <AddToTrip destination={destination}/>
    </div>
  </article>
}


