import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { App } from './App'

describe('App', () => {
  it('renders the Upload page as the landing route within the layout shell', () => {
    render(<App />)

    // Layout shell + navigation.
    expect(screen.getByRole('heading', { name: /ai sast platform/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /upload/i })).toBeInTheDocument()

    // Upload landing page.
    expect(screen.getByRole('heading', { name: /scan a repository/i })).toBeInTheDocument()
  })
})
