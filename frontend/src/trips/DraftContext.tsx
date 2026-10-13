import { createContext, useContext, useState, type ReactNode } from 'react'
import type { CatalogMode, Destination } from '../catalog/types'
import { emptyStore, readStore, storageKey, writeStore, type TripStore } from './storage'
export interface Stop { destination: Destination; minutes: number }
export interface Draft { name: string; date: string; stops: Stop[] }
const DraftContext = createContext<{
  stores: Record<CatalogMode, TripStore>; errors: Record<CatalogMode, string>
  change: (mode: CatalogMode, change: (store: TripStore) => TripStore, savedOnly?: boolean) => boolean
  reset: (mode: CatalogMode) => void
} | null>(null)
export function DraftProvider({ children }: { children: ReactNode }) {
  const [initial] = useState(() => ({ public: readStore('public'), fixtures: readStore('fixtures') }))
  const [stores, setStores] = useState({ public: initial.public.store, fixtures: initial.fixtures.store })
  const [errors, setErrors] = useState({ public: initial.public.error, fixtures: initial.fixtures.error })
  const [blocked, setBlocked] = useState({ public: !!initial.public.error, fixtures: !!initial.fixtures.error })
  function change(mode: CatalogMode, fn: (store: TripStore) => TripStore, savedOnly = false) {
    if (mode === 'fixtures' && !import.meta.env.DEV) return false
    const next = fn(stores[mode])
    let persisted = false
    if (!blocked[mode]) {
      try { writeStore(mode, next); persisted = true; setErrors(e => ({ ...e, [mode]: '' })) }
      catch { setErrors(e => ({ ...e, [mode]: 'Browser storage is unavailable or full. Changes remain in memory only; this trip was not saved.' })) }
    }
    if (!savedOnly || persisted) setStores(s => ({ ...s, [mode]: next }))
    return persisted
  }
  function reset(mode: CatalogMode) {
    if (mode === 'fixtures' && !import.meta.env.DEV) return
    try { localStorage.removeItem(storageKey(mode)); setStores(s => ({ ...s, [mode]: emptyStore() })); setBlocked(b => ({ ...b, [mode]: false })); setErrors(e => ({ ...e, [mode]: '' })) }
    catch { setErrors(e => ({ ...e, [mode]: 'Browser storage could not be reset.' })) }
  }
  return <DraftContext.Provider value={{ stores, errors, change, reset }}>{children}</DraftContext.Provider>
}
export function useDraft(mode: CatalogMode) {
  const c = useContext(DraftContext)
  if (!c) throw new Error('Trip draft provider is missing')
  const store = c.stores[mode]
  const saved = store.saved.find(t => t.id === store.activeId)
  return {
    draft: store.draft, savedTrips: store.saved, error: c.errors[mode],
    activeId: store.activeId, dirty: !saved || JSON.stringify(saved.draft) !== JSON.stringify(store.draft),
    update: (fn: (draft: Draft) => Draft) => c.change(mode, s => ({ ...s, draft: fn(s.draft) })),
    save: () => {
      if (!store.draft.name.trim()) return false
      const trip = { id: store.activeId || crypto.randomUUID(), updatedAt: new Date().toISOString(), draft: structuredClone(store.draft) }
      return c.change(mode, s => ({ ...s, activeId: trip.id, saved: [...s.saved.filter(t => t.id !== trip.id), trip] }), true)
    },
    open: (id: string) => c.change(mode, s => { const t = s.saved.find(t => t.id === id); return t ? { ...s, activeId: id, draft: structuredClone(t.draft) } : s }),
    startNew: () => c.change(mode, s => ({ ...s, draft: emptyStore().draft, activeId: null })),
    remove: (id: string) => c.change(mode, s => ({ ...s, saved: s.saved.filter(t => t.id !== id), activeId: s.activeId === id ? null : s.activeId }), true),
    reset: () => c.reset(mode),
  }
}


