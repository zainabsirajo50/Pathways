import { useId } from 'react'
import type { Category } from '../catalog/types'

// Original decorative artwork, not destination photography or geographic evidence.
export function Landscape({ category }: { category: Category }) {
  const id = useId().replace(/:/g, '')
  const water = ['waterfall', 'river', 'lake', 'coast'].includes(category)
  return <svg className={`landscape landscape-${category}`} viewBox="0 0 400 180" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
    <defs><linearGradient id={id} x2="0" y2="1"><stop stopColor="#c6d4c3"/><stop offset="1" stopColor="#e7dfca"/></linearGradient></defs>
    <path fill={`url(#${id})`} d="M0 0h400v180H0z"/><circle cx="315" cy="40" r="23" fill="#f3ebd7"/>
    <path d="M-20 145 75 46l74 74 84-98 190 131v45H-20Z" fill="#819a7c"/>
    <path d="m75 46 28 28-17-2-11 8-12-10-12 2Z" fill="#dce3d2"/>
    <path d="m-30 165 105-50 73 34 115-65 160 76v40H-30Z" fill="#476957"/>
    <path d="M-20 167q100-53 201 0t240-9v42H-20Z" fill="#244a3a"/>
    {water && <path d="M189 122q-20 28 31 34t-10 24h110q-36-29-75-32t-37-26Z" fill="#b7cdc5"/>}
    {[15, 37, 358, 382].map((x, i) => <g key={x} transform={`translate(${x} ${75+i*8})`}><path d="m0 0-16 52h32Z" fill="#1e4134"/><path d="M0 44v30" stroke="#1e4134" strokeWidth="4"/></g>)}
  </svg>
}
