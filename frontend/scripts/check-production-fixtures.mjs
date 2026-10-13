import { readdir, readFile } from 'node:fs/promises'

// Fail the build if development fixture identity or coordinate evidence leaks.
const forbidden = ['island-ford-preview', 'amicalola-preview', '33.994622', '-84.333933', 'unitdirections.htm']
for (const entry of await readdir(new URL('../dist/assets/', import.meta.url))) {
  if (!entry.endsWith('.js')) continue
  const bundle = await readFile(new URL(`../dist/assets/${entry}`, import.meta.url), 'utf8')
  if (forbidden.some(value => bundle.includes(value))) throw new Error(`Development fixture data found in production asset: ${entry}`)
}
console.log('Production fixture isolation check passed.')
