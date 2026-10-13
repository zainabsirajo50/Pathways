import { expect, it } from 'vitest'
import { fixtureDestinations, fixturePage } from './fixtures'
import { hasCoordinates } from '../components/DestinationMap'

it('includes only the supplied NPS entrance reference and never assigns other coordinates', () => {
  const points = fixtureDestinations.filter(hasCoordinates)
  expect(points).toHaveLength(1)
  expect(points[0]).toMatchObject({ slug: 'island-ford-preview', latitude: 33.994622, longitude: -84.333933,
    official_website: 'https://www.nps.gov/chat/planyourvisit/unitdirections.htm' })
  expect(points[0].access_notes).toContain('Routing verification has not been performed')
  expect(fixtureDestinations.filter(row => row !== points[0]).every(row => row.latitude === null && row.longitude === null)).toBe(true)
})
it('keeps coordinate-bearing fixtures synchronized with search, category and page results', () => {
  const resultPoints = (q = '', category: '' | 'river' | 'gorge' = '', page = 1) =>
    fixturePage({ q, category, page }).items.filter(hasCoordinates).map(row => row.slug)
  expect(resultPoints()).toEqual(['island-ford-preview'])
  expect(resultPoints('Island')).toEqual(['island-ford-preview'])
  expect(resultPoints('Falls')).toEqual([])
  expect(resultPoints('', 'river')).toEqual(['island-ford-preview'])
  expect(resultPoints('', 'gorge')).toEqual([])
  expect(resultPoints('', '', 2)).toEqual([])
  expect(fixturePage({ q: '', category: '', page: 1 }).items).toHaveLength(6)
})
