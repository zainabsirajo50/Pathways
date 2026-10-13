import { render, screen, within, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router'
import { afterEach, expect, it, vi } from 'vitest'
import { App } from './App'

function mount(url: string) {
  render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><MemoryRouter initialEntries={[url]}><App /></MemoryRouter></QueryClientProvider>)
}
afterEach(() => { vi.unstubAllEnvs(); vi.unstubAllGlobals(); window.history.replaceState({}, '', '/') })

it('shows an empty draft with editable name and optional date', async () => {
  mount('/trips/new')
  expect(screen.getByText('0 stops')).toBeVisible()
  expect(screen.getByText('Start with a place.')).toBeVisible()
  const user = userEvent.setup()
  await user.type(screen.getByLabelText('Trip name'), 'A Georgia day')
  expect(screen.getByLabelText('Trip name')).toHaveValue('A Georgia day')
  expect(screen.getByLabelText('Trip date (optional)')).toHaveValue('')
  fireEvent.change(screen.getByLabelText('Trip date (optional)'), { target: { value: '2026-10-20' } })
  expect(screen.getByLabelText('Trip date (optional)')).toHaveValue('2026-10-20')
})

it('adds from Explore and details, retains navigation state, reorders, edits duration and removes', async () => {
  const fetchMock = vi.fn()
  vi.stubGlobal('fetch', fetchMock)
  mount('/explore?preview=1')
  const user = userEvent.setup()
  await user.click(await screen.findByRole('button', { name: 'Add Amicalola Falls to trip' }))
  expect(screen.getByRole('button', { name: 'Added Amicalola Falls to draft' })).toBeDisabled()
  await user.click(screen.getByRole('link', { name: 'Island Ford' }))
  await user.click(await screen.findByRole('button', { name: 'Add Island Ford to trip' }))
  await user.click(screen.getByRole('link', { name: 'Open draft →' }))
  expect(screen.getByText('2 stops')).toBeVisible()
  expect(screen.getByText('120 minutes planned visiting · excludes travel')).toBeVisible()
  expect(screen.getByText('Not mapped · coordinates unavailable')).toBeVisible()
  expect(screen.getByText('Mapped reference · routing untested')).toBeVisible()
  await user.type(screen.getByLabelText('Trip name'), 'My outdoor day')
  fireEvent.change(screen.getByLabelText('Trip date (optional)'), { target: { value: '2026-10-20' } })
  await user.click(screen.getByRole('button', { name: 'Move Island Ford up' }))
  const stops = screen.getByRole('list').querySelectorAll('li')
  expect(within(stops[0]).getByRole('link', { name: 'Island Ford' })).toBeVisible()
  await user.clear(screen.getByLabelText('Visit duration for Island Ford'))
  await user.type(screen.getByLabelText('Visit duration for Island Ford'), '90')
  expect(screen.getByText('150 minutes planned visiting · excludes travel')).toBeVisible()
  await user.click(screen.getByRole('link', { name: 'Explore' }))
  await screen.findByRole('button', { name: 'Added Island Ford to draft' })
  await user.click(screen.getByRole('link', { name: 'Day trips' }))
  expect(screen.getByLabelText('Trip name')).toHaveValue('My outdoor day')
  expect(screen.getByLabelText('Trip date (optional)')).toHaveValue('2026-10-20')
  expect(screen.getByLabelText('Visit duration for Island Ford')).toHaveValue(90)
  await user.click(screen.getByRole('button', { name: 'Remove Amicalola Falls' }))
  expect(screen.getByText('1 stop')).toBeVisible()
  expect(fetchMock).not.toHaveBeenCalled()
})

it('keeps public and development drafts separate and rejects invalid durations', async () => {
  vi.stubGlobal('fetch', vi.fn())
  mount('/explore?preview=1')
  const user = userEvent.setup()
  await user.click(await screen.findByRole('button', { name: 'Add Amicalola Falls to trip' }))
  await user.click(screen.getByRole('link', { name: 'Open draft →' }))
  await user.clear(screen.getByLabelText('Visit duration for Amicalola Falls'))
  await user.type(screen.getByLabelText('Visit duration for Amicalola Falls'), '0')
  expect(screen.getByRole('alert')).toHaveTextContent('Enter whole minutes')
  expect(screen.getByText('60 minutes planned visiting · excludes travel')).toBeVisible()
  await user.click(screen.getByRole('link', { name: 'Pathways home' }))
  await user.click(screen.getByRole('link', { name: 'Day trips' }))
  expect(screen.getByText('0 stops')).toBeVisible()
  expect(screen.queryByText('Amicalola Falls')).toBeNull()
})

it('ignores development draft parameters in production', () => {
  vi.stubEnv('DEV', false)
  mount('/trips/new?preview=1')
  expect(screen.getByText('Browser trip draft')).toBeVisible()
  expect(screen.queryByText('Development preview trip · fixture stops only')).toBeNull()
  expect(screen.getByText('0 stops')).toBeVisible()
})


