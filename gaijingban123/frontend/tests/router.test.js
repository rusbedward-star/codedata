import { describe, expect, test } from 'vitest'

import router from '../src/router'

describe('router', () => {
  test('registers all main routes', () => {
    const paths = router.getRoutes().map((route) => route.path)

    expect(paths).toContain('/')
    expect(paths).toContain('/data-center')
    expect(paths).toContain('/metrics')
    expect(paths).toContain('/forecast')
    expect(paths).toContain('/charts')
    expect(paths).toContain('/system')
  })
})
