import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider } from 'react-router'
import { QueryProvider } from '@/app/providers/QueryProvider'
import { router } from '@/app/router'
import { MOCKS_ENABLED } from '@/shared/config'
import '@/styles/index.css'

async function bootstrap() {
  // MSW включается флагом VITE_ENABLE_MOCKS (§2). В dev — всегда; для демо-стенда
  // (linkavto.awwwdde.art) флаг ставится и в прод-сборке, чтобы витрина работала
  // без бэкенда. Динамический импорт → в бандл попадает отдельным чанком и грузится
  // только когда флаг включён.
  if (MOCKS_ENABLED) {
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
