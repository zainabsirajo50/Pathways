import { ApiError, fetchCategories, fetchDestination, fetchDestinations } from './api'
import { type CatalogMode, type Filters } from './types'

// Vite removes this branch and its dynamic import in production builds.
// No silent fallback from a failed or empty public API request to fixtures.
async function developmentFixtures() {
  if (import.meta.env.DEV) return import('../dev/fixtures')
  throw new Error('Preview fixtures are available only in development.')
}
export async function loadDestinations(mode: CatalogMode, filters: Filters, signal?: AbortSignal) {
  if (mode === 'fixtures') return (await developmentFixtures()).fixturePage(filters)
  return fetchDestinations(filters, signal)
}
export async function loadCategories(mode: CatalogMode, signal?: AbortSignal) {
  if (mode === 'fixtures') return (await developmentFixtures()).fixtureCategories
  return fetchCategories(signal)
}

export async function loadDestination(mode: CatalogMode, slug: string, signal?: AbortSignal) {
  if (mode === 'fixtures') {
    const item = (await developmentFixtures()).fixtureDestinations.find(row => row.slug === slug)
    if (!item) throw new ApiError(404, 'Destination not found')
    return item
  }
  return fetchDestination(slug, signal)
}
