import { isDestination } from '../catalog/api'
import type { CatalogMode } from '../catalog/types'
import type { Draft } from './DraftContext'
export interface SavedTrip { id: string; updatedAt: string; draft: Draft }
export interface TripStore { draft: Draft; activeId: string | null; saved: SavedTrip[] }
export const emptyStore = (): TripStore => ({ draft: { name: '', date: '', stops: [] }, activeId: null, saved: [] })
export const storageKey = (mode: CatalogMode) => `pathways.trips.v1.${mode}`
function validDraft(value: unknown): value is Draft {
  if (!value || typeof value !== 'object') return false
  const d = value as Draft
  return typeof d.name === 'string' && d.name.length <= 120 && typeof d.date === 'string' &&
    (d.date === '' || /^\d{4}-\d{2}-\d{2}$/.test(d.date) && !Number.isNaN(Date.parse(d.date)) && new Date(d.date).toISOString().slice(0, 10) === d.date) &&
    Array.isArray(d.stops) && d.stops.length <= 100 && d.stops.every(s => s && isDestination(s.destination) && s.destination.slug.length > 0 && s.destination.name.length > 0 && Number.isInteger(s.minutes) && s.minutes >= 1 && s.minutes <= 1440) &&
    new Set(d.stops.map(s => s.destination.slug)).size === d.stops.length
}
export function readStore(mode: CatalogMode): { store: TripStore; error: string } {
  if (mode === 'fixtures' && !import.meta.env.DEV) return { store: emptyStore(), error: '' }
  try {
    const raw = localStorage.getItem(storageKey(mode))
    if (!raw) return { store: emptyStore(), error: '' }
    const v = JSON.parse(raw)
    if (v.version !== 1 || v.mode !== mode || !validDraft(v.draft) || !Array.isArray(v.saved) || v.saved.length > 100 ||
      !v.saved.every((s: SavedTrip) => s && typeof s.id === 'string' && s.id.length > 0 && typeof s.updatedAt === 'string' && !Number.isNaN(Date.parse(s.updatedAt)) && validDraft(s.draft) && s.draft.name.trim().length > 0) ||
      new Set(v.saved.map((s: SavedTrip) => s.id)).size !== v.saved.length || !(v.activeId === null || v.saved.some((s: SavedTrip) => s.id === v.activeId))) throw new Error()
    return { store: { draft: v.draft, activeId: v.activeId, saved: v.saved }, error: '' }
  } catch { return { store: emptyStore(), error: 'Browser trip data could not be loaded (unavailable storage, malformed data, or unsupported version). It has not been overwritten. Use Reset browser trips to start again.' } }
}
export function writeStore(mode: CatalogMode, store: TripStore) {
  if (mode === 'fixtures' && !import.meta.env.DEV) throw new Error('Development storage unavailable')
  if (!validDraft(store.draft) || store.saved.length > 100) throw new Error('Trip size limit reached')
  localStorage.setItem(storageKey(mode), JSON.stringify({ version: 1, mode, ...store }))
}

