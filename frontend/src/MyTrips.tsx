import { useState, useEffect, useRef } from 'react'
import { Link, useLocation, useNavigate } from 'react-router'
import { useDraft } from './trips/DraftContext'
export function MyTrips() {
  useEffect(() => { document.title = 'My Trips · Pathways'; return () => { document.title = 'Explore Georgia · Pathways' } }, [])
  const preview = import.meta.env.DEV && new URLSearchParams(useLocation().search).get('preview') === '1'
  const suffix = preview ? '?preview=1' : ''
  const { savedTrips, draft, error, dirty, open, remove, startNew, reset } = useDraft(preview ? 'fixtures' : 'public')
  const navigate = useNavigate()
  const dialog = useRef<HTMLDialogElement>(null)
  const [pending, setPending] = useState<{ kind: 'delete' | 'open' | 'new' | 'reset'; id?: string } | null>(null)
  useEffect(() => { if (pending) dialog.current?.showModal() }, [pending])
  function proceed(action: NonNullable<typeof pending>) {
    if (action.kind === 'delete') remove(action.id!)
    else if (action.kind === 'reset') reset()
    else { if (action.kind === 'new') startNew(); else open(action.id!); navigate(`/trips/new${suffix}`) }
    setPending(null)
  }
  function request(action: NonNullable<typeof pending>) {
    if (action.kind === 'delete' || action.kind === 'reset' || dirty && (draft.name !== '' || draft.stops.length > 0 || draft.date !== '')) setPending(action)
    else proceed(action)
  }
  return <main id="main" className="trip-page"><section className="intro"><div><p className="eyebrow">ROOM FOR YOUR NEXT ESCAPE</p><h1>My <em>trips.</em></h1><p className="intro-copy">Stored only in this browser. No account sync or cloud backup.</p></div></section>
    {preview && <div className="dev-banner fixture-active">Development preview trips · separate from public trips</div>}
    {error && <div role="alert">{error}<button onClick={() => request({ kind: 'reset' })}>Reset browser trips</button></div>}
    <div className="stop-actions"><Link className="primary-button" to={`/trips/new${suffix}`}>Continue current draft</Link><button className="primary-button" onClick={() => request({ kind: 'new' })}>New trip</button></div>
    <p>{dirty ? 'Current draft has unsaved changes.' : 'Current trip matches its saved version.'}</p>
    {savedTrips.length === 0 ? <section className="catalog-state"><h2>No saved trips yet.</h2><p>Build a day trip, give it a name, and choose Save Trip.</p></section> : <ul className="saved-trips">{[...savedTrips].sort((a,b) => b.updatedAt.localeCompare(a.updatedAt)).map(t => <li key={t.id}><h2>{t.draft.name}</h2><p>{t.draft.date || 'No date selected'} · {t.draft.stops.length} stops · {t.draft.stops.reduce((n,s) => n+s.minutes,0)} minutes visiting</p><p>Saved {new Date(t.updatedAt).toLocaleString()}</p><div className="stop-actions"><button onClick={() => request({ kind: 'open', id: t.id })} aria-label={`Edit ${t.draft.name}`}>Open & edit</button><button onClick={() => request({ kind: 'delete', id: t.id })} aria-label={`Delete ${t.draft.name}`}>Delete</button></div></li>)}</ul>}
    {pending && <dialog ref={dialog} onCancel={() => setPending(null)} className="trip-confirm" role="alertdialog" aria-labelledby="confirm-title"><h2 id="confirm-title">{pending.kind === 'delete' ? 'Delete this saved trip?' : pending.kind === 'reset' ? 'Reset all trips in this mode?' : 'Replace the current unsaved draft?'}</h2><p>{pending.kind === 'delete' ? 'The saved copy will be removed. An open draft is retained.' : pending.kind === 'reset' ? 'This removes browser trips and the draft for this mode only.' : 'Unsaved changes will be discarded. Saved trips remain available.'}</p><button autoFocus onClick={() => setPending(null)}>Cancel</button><button onClick={() => proceed(pending)}>Confirm</button></dialog>}
  </main>
}


