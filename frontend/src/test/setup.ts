import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, beforeEach, vi } from 'vitest'
afterEach(() => cleanup())

// jsdom does not implement native modal dialog methods.
HTMLDialogElement.prototype.showModal = function () { this.setAttribute('open', '') }
HTMLDialogElement.prototype.close = function () { this.removeAttribute('open') }

beforeEach(() => { localStorage.clear(); vi.stubEnv('VITE_MAPBOX_ACCESS_TOKEN', '') })
afterEach(() => vi.unstubAllEnvs())


