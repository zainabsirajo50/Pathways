export const categories = ['waterfall', 'lake', 'gorge', 'forest', 'river', 'coast', 'mountain', 'garden', 'park'] as const
export type Category = typeof categories[number]
export type CatalogMode = 'public' | 'fixtures'

// Explicitly matches the public API; no ORM IDs, review fields, or entrances.
export interface Destination {
  slug: string
  name: string
  category: Category
  region: string
  city: string | null
  state: string
  description: string | null
  official_website: string | null
  access_notes: string | null
  latitude: number | null
  longitude: number | null
}
export interface DestinationPage {
  items: Destination[]
  total: number
  page: number
  page_size: number
}
export interface Filters {
  q: string
  category: Category | ''
  page: number
}
export const PAGE_SIZE = 6
export const label = (value: string) => value.charAt(0).toUpperCase() + value.slice(1)
