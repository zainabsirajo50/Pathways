import { categories, PAGE_SIZE, type Destination, type DestinationPage, type Filters } from '../catalog/types'

// UI examples only. Island Ford includes an NPS-published entrance reference,
// not a reviewed or route-tested endpoint. Never imported into the database.
export const fixtureCategories = [...categories]
export const fixtureDestinations: Destination[] = [
  ['amicalola-preview', 'Amicalola Falls', 'waterfall', 'Dawsonville', 'A cascade through the foothills, framed by woodland trails.'],
  ['black-rock-preview', 'Black Rock Mountain', 'mountain', 'Mountain City', 'Quiet forest paths and sweeping Blue Ridge horizons.'],
  ['cloudland-preview', 'Cloudland Canyon', 'gorge', 'Rising Fawn', 'Sandstone cliffs, deep green woods, and a canyon to explore.'],
  ['driftwood-preview', 'Driftwood Beach', 'coast', 'Jekyll Island', 'Sculptural driftwood meets the soft rhythm of the Atlantic.'],
  ['island-ford-preview', 'Island Ford', 'river', 'Sandy Springs', 'A slower afternoon beside the Chattahoochee River.'],
  ['providence-preview', 'Providence Canyon', 'gorge', 'Lumpkin', 'Warm earth tones and winding paths through a striking landscape.'],
  ['red-top-preview', 'Red Top Mountain', 'lake', 'Cartersville', 'Wooded shorelines and space to pause beside the water.'],
  ['skidaway-preview', 'Skidaway Island', 'forest', 'Savannah', 'Maritime forest, salt marsh, and coastal stillness.'],
  ['tallulah-preview', 'Tallulah Gorge', 'gorge', 'Tallulah Falls', 'A dramatic gorge in the heart of northeast Georgia.'],
  ['vogel-preview', 'Vogel State Park', 'park', 'Blairsville', 'Mountain scenery and a peaceful lake in the North Georgia woods.'],
].map(([slug, name, category, city, description]) => ({
  slug, name, category: category as Destination['category'], city, description,
  state: 'GA', region: 'Georgia',
  official_website: slug === 'island-ford-preview' ? 'https://www.nps.gov/chat/planyourvisit/unitdirections.htm' : null,
  access_notes: slug === 'island-ford-preview'
    ? 'NPS-published Island Ford entrance reference: 33.994622, -84.333933. Entrance, not visitor-center parking. Routing verification has not been performed; this fixture does not approve the destination or endpoint.' : null,
  latitude: slug === 'island-ford-preview' ? 33.994622 : null,
  longitude: slug === 'island-ford-preview' ? -84.333933 : null,
}))

export function fixturePage(filters: Filters): DestinationPage {
  const matches = fixtureDestinations.filter(row =>
    row.name.toLowerCase().includes(filters.q.trim().toLowerCase()) &&
    (!filters.category || row.category === filters.category))
    .sort((a, b) => a.name.toLowerCase().localeCompare(b.name.toLowerCase()) || a.slug.localeCompare(b.slug))
  return { items: matches.slice((filters.page - 1) * PAGE_SIZE, filters.page * PAGE_SIZE),
    total: matches.length, page: filters.page, page_size: PAGE_SIZE }
}
