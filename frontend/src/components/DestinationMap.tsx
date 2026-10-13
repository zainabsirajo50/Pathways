import { useEffect, useRef, useState } from 'react'
import type { Map as MapboxMap } from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'
import type { Destination } from '../catalog/types'

export function hasCoordinates(destination: Destination): boolean {
  return typeof destination.latitude === 'number' && Number.isFinite(destination.latitude) && Math.abs(destination.latitude) <= 90 &&
    typeof destination.longitude === 'number' && Number.isFinite(destination.longitude) && Math.abs(destination.longitude) <= 180
}

export function DestinationMap({ destinations, selected, onSelect, fixtures, loading, numbered = false }: {
  destinations: Destination[]; selected?: Destination; onSelect: (slug: string) => void; fixtures: boolean; loading: boolean; numbered?: boolean
}) {
  const container = useRef<HTMLDivElement>(null)
  const map = useRef<MapboxMap | null>(null)
  const renderer = useRef<typeof import('mapbox-gl').default | null>(null)
  const callback = useRef(onSelect)
  callback.current = onSelect
  const [state, setState] = useState<'loading' | 'ready' | 'error'>('loading')
  const [attempt, setAttempt] = useState(0)
  const token = (import.meta.env.VITE_MAPBOX_ACCESS_TOKEN ?? '').trim()
  const validToken = token.startsWith('pk.')
  const points = destinations.filter(hasCoordinates)

  useEffect(() => {
    if (!validToken || !container.current) return
    const element = container.current
    setState('loading')
    let instance: MapboxMap | undefined
    let observer: ResizeObserver | undefined
    let cancelled = false
    const timeout = window.setTimeout(() => setState('error'), 20_000)
    void import('mapbox-gl').then(({ default: mapboxgl }) => {
    if (cancelled) return
    renderer.current = mapboxgl
    try {
      instance = new mapboxgl.Map({ container: element, accessToken: token,
        style: 'mapbox://styles/mapbox/outdoors-v12', center: [-83.5, 32.6], zoom: 6.3,
        attributionControl: true })
      map.current = instance
      instance.addControl(new mapboxgl.NavigationControl({ showCompass: false }), 'top-right')
      instance.on('load', () => { window.clearTimeout(timeout); setState('ready') })
      instance.on('error', () => { window.clearTimeout(timeout); setState('error') })
      observer = new ResizeObserver(() => instance?.resize())
      observer.observe(element)
    } catch { window.clearTimeout(timeout); setState('error') }
    }).catch(() => { if (!cancelled) { window.clearTimeout(timeout); setState('error') } })
    return () => { cancelled = true; window.clearTimeout(timeout); observer?.disconnect(); instance?.remove(); map.current = null }
  }, [token, validToken, attempt])

  useEffect(() => {
    if (!map.current || !renderer.current || state !== 'ready') return
    const mapboxgl = renderer.current
    const markers = destinations.filter(hasCoordinates).map(destination => {
      const button = document.createElement('button')
      button.type = 'button'
      button.className = `destination-marker${destination.slug === selected?.slug ? ' marker-selected' : ''}`
      button.setAttribute('aria-label', `Select ${destination.name} on map`)
      button.setAttribute('aria-pressed', String(destination.slug === selected?.slug))
      button.textContent = numbered ? String(destinations.findIndex(row => row.slug === destination.slug) + 1) : '↟'
      button.onclick = () => callback.current(destination.slug)
      const marker = new mapboxgl.Marker({ element: button })
        .setLngLat([destination.longitude!, destination.latitude!]).addTo(map.current!)
      // Mapbox assigns role=img to custom markers; restore the interactive role.
      button.setAttribute('role', 'button')
      button.tabIndex = 0
      return marker
    })
    return () => { markers.forEach(marker => marker.remove()) }
  }, [destinations, selected?.slug, state, numbered])

  useEffect(() => {
    if (state === 'ready' && selected && hasCoordinates(selected)) {
      map.current?.easeTo({ center: [selected.longitude!, selected.latitude!], zoom: 10,
        duration: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 650 })
    }
  }, [selected, state])

  return <>
    <div ref={container} className="interactive-map" role="region" aria-label="Interactive Georgia destination map" />
    {!validToken ? <div className="map-status" role="status"><strong>Map setup needed</strong><p>Add a public Mapbox token to VITE_MAPBOX_ACCESS_TOKEN in frontend/.env.local, then restart Vite.</p></div>
      : state === 'error' ? <div className="map-status" role="alert"><strong>The map could not load.</strong><p>Check your token, its allowed URLs, your connection, and WebGL support.</p><button className="text-button" onClick={() => setAttempt(value => value + 1)}>Retry map</button></div>
      : state === 'loading' ? <div className="map-status" role="status">Loading Georgia’s map…</div>
      : <div className="map-caption" role="status">{loading ? 'Updating destinations…' : points.length === 0 ? 'No display coordinates in these results. Places remain available in the list.' : fixtures ? `${points.length} published entrance reference · routing untested` : `${points.length} display ${points.length === 1 ? 'point' : 'points'} · not routing entrances`}{fixtures && <span>Development fixtures · no verified destination coordinates</span>}</div>}
  </>
}

