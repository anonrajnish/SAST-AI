import { RouterProvider, createBrowserRouter } from 'react-router-dom'

import { Layout } from './components/layout/Layout'
import { StatusPage } from './pages/StatusPage'

const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [{ index: true, element: <StatusPage /> }],
  },
])

export function App() {
  return <RouterProvider router={router} />
}
