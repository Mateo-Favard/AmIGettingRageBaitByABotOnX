import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useAnalysis } from '~/composables/useAnalysis'
import type { AnalyzeResponse } from '~/composables/useAnalysis'

const mockResponse: AnalyzeResponse = {
  handle: 'testuser',
  composite_score: 72.5,
  scores: {
    ai_content_score: 85,
    behavioral_score: 42,
    sentiment_score: 15,
    political_shift_score: 70,
    network_score: null,
  },
  profile: {
    handle: 'testuser',
    display_name: 'Test User',
    bio: 'A test bio',
    followers_count: 1234,
    following_count: 567,
    tweets_count: 8901,
    profile_image_url: 'https://example.com/avatar.jpg',
    account_created_at: '2020-01-01T00:00:00Z',
  },
  analyzed_at: '2026-03-08T12:00:00Z',
  cached: false,
}

// Mock $fetch globally
const mockFetch = vi.fn()
vi.stubGlobal('$fetch', mockFetch)

describe('useAnalysis', () => {
  beforeEach(() => {
    mockFetch.mockReset()
  })

  it('starts with clean state', () => {
    const { state } = useAnalysis()
    expect(state.data).toBeNull()
    expect(state.loading).toBe(false)
    expect(state.error).toBeNull()
  })

  it('sets loading while fetching', async () => {
    mockFetch.mockImplementation(() => new Promise(() => {})) // never resolves
    const { state, analyzeByHandle } = useAnalysis()

    analyzeByHandle('testuser') // don't await
    // Need a tick for the async function to start
    await new Promise(r => setTimeout(r, 0))

    expect(state.loading).toBe(true)
    expect(state.data).toBeNull()
    expect(state.error).toBeNull()
  })

  it('sets data on success', async () => {
    mockFetch.mockResolvedValue(mockResponse)
    const { state, analyzeByHandle } = useAnalysis()

    const result = await analyzeByHandle('testuser')

    expect(state.loading).toBe(false)
    expect(state.data).toEqual(mockResponse)
    expect(state.error).toBeNull()
    expect(result).toEqual(mockResponse)
  })

  it('constructs correct URL from handle', async () => {
    mockFetch.mockResolvedValue(mockResponse)
    const { analyzeByHandle } = useAnalysis()

    await analyzeByHandle('testuser')

    expect(mockFetch).toHaveBeenCalledWith(
      '/api/analyze',
      {
        method: 'POST',
        body: { url: 'https://x.com/testuser' },
      },
    )
  })

  it('sets error on failure', async () => {
    mockFetch.mockRejectedValue({
      data: { error: { message: 'Compte non trouvé' } },
    })
    const { state, analyzeByHandle } = useAnalysis()

    const result = await analyzeByHandle('testuser')

    expect(state.loading).toBe(false)
    expect(state.data).toBeNull()
    expect(state.error).toBe('Compte non trouvé')
    expect(result).toBeNull()
  })

  it('falls back to generic error message', async () => {
    mockFetch.mockRejectedValue({})
    const { state, analyzeByHandle } = useAnalysis()

    await analyzeByHandle('testuser')

    expect(state.error).toBe("Une erreur est survenue lors de l'analyse.")
  })

  it('resets state', async () => {
    mockFetch.mockResolvedValue(mockResponse)
    const { state, analyzeByHandle, reset } = useAnalysis()

    await analyzeByHandle('testuser')
    expect(state.data).not.toBeNull()

    reset()
    expect(state.data).toBeNull()
    expect(state.loading).toBe(false)
    expect(state.error).toBeNull()
  })
})
