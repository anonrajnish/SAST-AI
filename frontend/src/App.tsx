import { RouterProvider, createBrowserRouter } from 'react-router-dom'

import { Layout } from './components/layout/Layout'
import { UploadPage } from './pages/UploadPage'

const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [{ index: true, element: <UploadPage /> }],
  },
])

export function App() {
  return <RouterProvider router={router} />
}
