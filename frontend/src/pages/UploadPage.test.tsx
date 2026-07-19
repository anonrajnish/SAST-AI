import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import { UploadPage } from './UploadPage'

function zipFile(name = 'repo.zip'): File {
  return new File(['PK pretend zip'], name, { type: 'application/zip' })
}

describe('UploadPage', () => {
  it('renders the primary workflow heading', () => {
    render(<UploadPage />)

    expect(screen.getByRole('heading', { name: /scan a repository/i })).toBeInTheDocument()
  })

  it('defaults the tech stack to Auto Detect', () => {
    render(<UploadPage />)

    expect(screen.getByRole('radio', { name: /auto detect/i })).toBeChecked()
  })

  it('disables the Scan button until a file is chosen', async () => {
    render(<UploadPage />)
    const scanButton = screen.getByRole('button', { name: /scan/i })
    expect(scanButton).toBeDisabled()

    await userEvent.upload(screen.getByLabelText(/repository archive/i), zipFile())

    expect(scanButton).toBeEnabled()
    expect(screen.getByText('repo.zip', { exact: false })).toBeInTheDocument()
  })

  it('shows a human-readable size for the selected archive', async () => {
    render(<UploadPage />)

    const bigZip = new File([new Uint8Array(1_572_864)], 'big.zip', { type: 'application/zip' })
    await userEvent.upload(screen.getByLabelText(/repository archive/i), bigZip)

    expect(screen.getByText(/1\.5 MB/)).toBeInTheDocument()
  })

  it('rejects a non-zip file and keeps the Scan button disabled', async () => {
    render(<UploadPage />)

    const notAZip = new File(['hello'], 'notes.txt', { type: 'text/plain' })
    // Bypass the input's `accept` filter (a browser hint only; drag-drop can bypass it too) so the
    // component's own extension guard is exercised.
    await userEvent.upload(screen.getByLabelText(/repository archive/i), notAZip, {
      applyAccept: false,
    })

    expect(screen.getByRole('alert')).toHaveTextContent(/\.zip archive/i)
    expect(screen.getByRole('button', { name: /scan/i })).toBeDisabled()
  })

  it('shows the stub notice when Scan is clicked (no backend wiring yet)', async () => {
    render(<UploadPage />)

    await userEvent.upload(screen.getByLabelText(/repository archive/i), zipFile())
    await userEvent.click(screen.getByRole('button', { name: /scan/i }))

    expect(screen.getByRole('status')).toHaveTextContent(/next slice/i)
  })
})
