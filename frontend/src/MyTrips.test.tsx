import { render, screen, cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router'
import { expect, it, vi } from 'vitest'
import { App } from './App'
import { readStore, storageKey } from './trips/storage'
function mount(url: string) { render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><MemoryRouter initialEntries={[url]}><App/></MemoryRouter></QueryClientProvider>) }
it('saves, reloads, reopens, edits and confirms deletion while isolating preview trips', async () => {
  const user = userEvent.setup()
  const fetch = vi.fn(); vi.stubGlobal('fetch', fetch)
  mount('/explore?preview=1')
  await user.click(await screen.findByRole('button', { name: 'Add Amicalola Falls to trip' }))
  await user.click(screen.getByRole('link', { name: 'Open draft →' }))
  await user.type(screen.getByLabelText('Trip name'), 'Forest day')
  await user.click(screen.getByRole('button', { name: 'Save Trip' }))
  expect(readStore('fixtures').store.saved).toHaveLength(1)
  cleanup(); mount('/trips/new?preview=1')
  expect(screen.getByLabelText('Trip name')).toHaveValue('Forest day')
  await user.clear(screen.getByLabelText('Visit duration for Amicalola Falls'))
  await user.type(screen.getByLabelText('Visit duration for Amicalola Falls'), '90')
  expect(screen.getByText('Unsaved changes to saved trip')).toBeVisible()
  expect(readStore('fixtures').store.saved[0].draft.stops[0].minutes).toBe(60)
  await user.click(screen.getByRole('button', { name: 'Save Trip' }))
  await user.click(screen.getByRole('link', { name: 'My Trips' }))
  await user.click(screen.getByRole('button', { name: 'Edit Forest day' }))
  expect(screen.getByLabelText('Visit duration for Amicalola Falls')).toHaveValue(90)
  await user.click(screen.getByRole('link', { name: 'My Trips' }))
  await user.click(screen.getByRole('button', { name: 'Delete Forest day' }))
  await user.click(screen.getByRole('button', { name: 'Cancel' }))
  expect(screen.getByRole('button', { name: 'Edit Forest day' })).toBeVisible()
  await user.click(screen.getByRole('button', { name: 'Delete Forest day' }))
  await user.click(screen.getByRole('button', { name: 'Confirm' }))
  expect(screen.getByText('No saved trips yet.')).toBeVisible()
  expect(readStore('fixtures').store.draft.stops).toHaveLength(1)
  expect(readStore('public').store.saved).toHaveLength(0)
  expect(readStore('public').store.draft.stops).toHaveLength(0)
  expect(fetch).not.toHaveBeenCalled(); vi.unstubAllGlobals()
})
it('retains draft edits across reload without explicitly saving', async () => {
  mount('/trips/new'); await userEvent.type(screen.getByLabelText('Trip name'), 'Unsaved name')
  cleanup(); mount('/trips/new')
  expect(screen.getByLabelText('Trip name')).toHaveValue('Unsaved name')
  expect(screen.getByText('Unsaved draft')).toBeVisible()
  expect(readStore('public').store.saved).toHaveLength(0)
})
it.each(['{bad', JSON.stringify({ version: 0 }), JSON.stringify({ version: 1, mode: 'fixtures', draft: {}, saved: [] })])('preserves malformed or outdated storage until explicit reset: %s', async raw => {
  localStorage.setItem(storageKey('public'), raw)
  mount('/trips')
  expect(screen.getByRole('alert')).toHaveTextContent('could not be loaded')
  await userEvent.click(screen.getByRole('button', { name: 'Reset browser trips' }))
  expect(localStorage.getItem(storageKey('public'))).toBe(raw)
  await userEvent.click(screen.getByRole('button', { name: 'Confirm' }))
  expect(localStorage.getItem(storageKey('public'))).toBeNull()
})
it('reports unavailable storage and never reports saving success', async () => {
  vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('quota') })
  mount('/trips/new'); await userEvent.type(screen.getByLabelText('Trip name'), 'My day')
  await userEvent.click(screen.getByRole('button', { name: 'Save Trip' }))
  expect(screen.getByRole('alert')).toHaveTextContent('not saved')
  expect(screen.queryByText('Trip saved in this browser.')).toBeNull()
})
it('ignores preview storage in production', () => {
  localStorage.setItem(storageKey('fixtures'), '{bad')
  vi.stubEnv('DEV', false); mount('/trips?preview=1')
  expect(screen.queryByRole('alert')).toBeNull()
  expect(screen.queryByText(/Development preview trips/)).toBeNull()
})

it('keeps unavailable public destination snapshots and asks before replacing unsaved edits', async () => {
  const destination = { slug: 'old-place', name: 'Old place', category: 'park', region: 'Georgia', city: null, state: 'GA', description: null, official_website: null, access_notes: null, latitude: null, longitude: null }
  const draft = { name: 'Saved outing', date: '2026-10-20', stops: [{ destination, minutes: 75 }] }
  localStorage.setItem(storageKey('public'), JSON.stringify({ version: 1, mode: 'public', draft: { ...draft, name: 'Changed outing' }, activeId: 'one', saved: [{ id: 'one', updatedAt: '2026-10-12T12:00:00Z', draft }] }))
  const fetch = vi.fn().mockResolvedValue({ ok: false, status: 404 }); vi.stubGlobal('fetch', fetch)
  mount('/trips')
  await userEvent.click(screen.getByRole('button', { name: 'Edit Saved outing' }))
  expect(screen.getByRole('alertdialog')).toHaveTextContent('Replace the current unsaved draft')
  await userEvent.click(screen.getByRole('button', { name: 'Cancel' }))
  expect(readStore('public').store.draft.name).toBe('Changed outing')
  await userEvent.click(screen.getByRole('button', { name: 'Edit Saved outing' }))
  await userEvent.click(screen.getByRole('button', { name: 'Confirm' }))
  expect(await screen.findByText(/Currently unavailable or catalog unreachable/)).toBeVisible()
  expect(screen.getByRole('link', { name: 'Old place' })).toBeVisible()
  expect(readStore('public').store.saved[0].draft).toEqual(draft)
  expect(screen.getByLabelText('Visit duration for Old place')).toHaveValue(75)
  vi.unstubAllGlobals()
})
it('rejects invalid stop durations and out-of-range coordinates without overwriting', () => {
  const destination = { slug: 'x', name: 'Place', category: 'park', region: 'Georgia', city: null, state: 'GA', description: null, official_website: null, access_notes: null, latitude: 200, longitude: null }
  const value = { version: 1, mode: 'public', draft: { name: '', date: '', stops: [{ destination, minutes: -1 }] }, activeId: null, saved: [] }
  const raw = JSON.stringify(value); localStorage.setItem(storageKey('public'), raw)
  expect(readStore('public').error).not.toBe('')
  expect(localStorage.getItem(storageKey('public'))).toBe(raw)
})
