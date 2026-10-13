import { useQuery } from '@tanstack/react-query'
import { loadDestination } from '../catalog/data'
import type { CatalogMode } from '../catalog/types'
export function Availability({ slug, mode }: { slug: string; mode: CatalogMode }) {
  const result = useQuery({ queryKey: ['destination', mode, slug], queryFn: ({ signal }) => loadDestination(mode, slug, signal), retry: false })
  return <p className="details-muted">{result.isPending ? 'Checking current catalog…' : result.isError ? 'Currently unavailable or catalog unreachable. Saved information is retained; check access before visiting.' : 'Saved destination snapshot. Current details may differ; check the destination page before visiting.'}</p>
}
