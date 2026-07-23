import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider } from 'react-router'
import { QueryProvider } from '@/app/providers/QueryProvider'
import { router } from '@/app/router'
import { MOCKS_ENABLED } from '@/shared/config'
import '@/styles/index.css'

async function bootstrap() {
  // import.meta.env.DEV даёт Vite вырезать MSW из прод-бандла целиком (§12).
  if (import.meta.env.DEV && MOCKS_ENABLED) {
    const { startMocks } = await import('@/mocks/browser')
    await startMocks()
  }

  const container = document.getElementById('root')
  if (!container) throw new Error('Не найден корневой элемент #root')

  createRoot(container).render(
    <StrictMode>
      <QueryProvider>
        <RouterProvider router={router} />
      </QueryProvider>
    </StrictMode>,
  )
}

void bootstrap()
