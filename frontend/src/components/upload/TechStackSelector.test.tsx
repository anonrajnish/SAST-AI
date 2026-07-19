import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { TechStackSelector } from './TechStackSelector'

describe('TechStackSelector', () => {
  it('renders the three tech-stack options', () => {
    render(<TechStackSelector value="auto" onChange={() => {}} />)

    expect(screen.getByRole('radio', { name: /auto detect/i })).toBeInTheDocument()
    expect(screen.getByRole('radio', { name: /python/i })).toBeInTheDocument()
    expect(screen.getByRole('radio', { name: /web/i })).toBeInTheDocument()
  })

  it('checks the radio matching the current value', () => {
    render(<TechStackSelector value="python" onChange={() => {}} />)

    expect(screen.getByRole('radio', { name: /python/i })).toBeChecked()
    expect(screen.getByRole('radio', { name: /auto detect/i })).not.toBeChecked()
  })

  it('calls onChange with the selected value', async () => {
    const onChange = vi.fn()
    render(<TechStackSelector value="auto" onChange={onChange} />)

    await userEvent.click(screen.getByRole('radio', { name: /web/i }))

    expect(onChange).toHaveBeenCalledWith('web')
  })

  it('disables every option when disabled', () => {
    render(<TechStackSelector value="auto" onChange={() => {}} disabled />)

    expect(screen.getByRole('radio', { name: /auto detect/i })).toBeDisabled()
    expect(screen.getByRole('radio', { name: /python/i })).toBeDisabled()
  })
})
