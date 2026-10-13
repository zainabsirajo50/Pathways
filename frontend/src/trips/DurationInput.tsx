import { useState } from 'react'

export function DurationInput({ name, minutes, onChange }: { name: string; minutes: number; onChange: (minutes: number) => void }) {
  const [text, setText] = useState(String(minutes))
  const number = Number(text)
  const valid = text !== '' && Number.isInteger(number) && number >= 1 && number <= 1440
  return <label className="duration-label">Visit duration (minutes)<input type="number" min={1} max={1440} step={1} value={text} aria-label={`Visit duration for ${name}`} aria-invalid={!valid}
    onChange={event => { setText(event.target.value); const value = event.target.valueAsNumber; if (Number.isInteger(value) && value >= 1 && value <= 1440) onChange(value) }}
    onBlur={() => { if (!valid) setText(String(minutes)) }}/>
    {!valid && <span role="alert">Enter whole minutes from 1 to 1440. The previous duration is retained until valid.</span>}
  </label>
}
