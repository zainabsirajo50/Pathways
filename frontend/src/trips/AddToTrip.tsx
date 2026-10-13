import { Link, useLocation } from 'react-router'
import type { Destination } from '../catalog/types'
import { useDraft } from './DraftContext'

export function AddToTrip({ destination }: { destination: Destination }) {
  const { search } = useLocation()
  const preview = import.meta.env.DEV && new URLSearchParams(search).get('preview') === '1'
  const { draft, update } = useDraft(preview ? 'fixtures' : 'public')
  const added = draft.stops.some(stop => stop.destination.slug === destination.slug)
  return <div className="add-trip-control"><button className="text-button" disabled={added} aria-label={`${added ? 'Added' : 'Add'} ${destination.name} ${added ? 'to draft' : 'to trip'}`} onClick={() => update(current => current.stops.some(stop => stop.destination.slug === destination.slug) ? current : { ...current, stops: [...current.stops, { destination, minutes: 60 }] })}>{added ? 'Added to draft ✓' : 'Add to Trip +'}</button>
    {added && <Link to={`/trips/new${preview ? '?preview=1' : ''}`}>Open draft →</Link>}
  </div>
}
