import { categories, PAGE_SIZE, type Category, type Destination, type DestinationPage, type Filters } from './types'

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message) }
}
const base = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

async function request(path: string, signal?: AbortSignal): Promise<unknown> {
  const response = await fetch(`${base}/api/v1/${path}`, { signal, credentials: 'omit' })
  if (!response.ok) {
    throw new ApiError(response.status, response.status === 422
      ? 'These filters could not be accepted. Try clearing your search.'
      : 'The destination catalog is unavailable. Please try again.')
  }
  return response.json()
}

export function isDestination(value: unknown): value is Destination {
  if (!value || typeof value !== 'object') return false
  const row = value as Record<string, unknown>
  const nullableText = (key: string) => row[key] === null || typeof row[key] === 'string'
  const coordinate = (key: string, bound: number) => row[key] === null ||
    (typeof row[key] === 'number' && Number.isFinite(row[key]) && Math.abs(row[key]) <= bound)
  return ['slug', 'name', 'region', 'state'].every(key => typeof row[key] === 'string') &&
    categories.includes(row.category as Category) &&
    ['city', 'description', 'official_website', 'access_notes'].every(nullableText) &&
    coordinate('latitude', 90) && coordinate('longitude', 180)
}

export async function fetchDestinations(filters: Filters, signal?: AbortSignal): Promise<DestinationPage> {
  const params = new URLSearchParams({ page: String(filters.page), page_size: String(PAGE_SIZE) })
  if (filters.q.trim()) params.set('q', filters.q.trim())
  if (filters.category) params.set('category', filters.category)
  const value = await request(`destinations?${params}`, signal) as DestinationPage
  if (!value || !Array.isArray(value.items) || !value.items.every(isDestination) ||
    !Number.isInteger(value.total) || value.total < 0 || value.page !== filters.page || value.page_size !== PAGE_SIZE) {
    throw new Error('The catalog returned an unexpected response. Please try again.')
  }
  return value
}

export async function fetchCategories(signal?: AbortSignal): Promise<Category[]> {
  const value = await request('destinations/categories', signal) as { categories?: unknown }
  if (!value || !Array.isArray(value.categories) || !value.categories.every(item => categories.includes(item))) {
    throw new Error('The category list could not be loaded.')
  }
  return value.categories as Category[]
}

export async function fetchDestination(slug: string, signal?: AbortSignal): Promise<Destination> {
  const value = await request(`destinations/${encodeURIComponent(slug)}`, signal)
  if (!isDestination(value) || value.slug !== slug) throw new Error('The destination returned an unexpected response.')
  return value
}
