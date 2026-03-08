export interface ScoreBreakdown {
  ai_content_score: number | null
  behavioral_score: number | null
  sentiment_score: number | null
  opportunism_score: number | null
}

export interface ProfileSummary {
  handle: string
  display_name: string
  bio: string
  followers_count: number
  following_count: number
  tweets_count: number
  profile_image_url: string
  account_created_at: string | null
}

export interface AnalyzeResponse {
  handle: string
  composite_score: number
  scores: ScoreBreakdown
  profile: ProfileSummary
  analyzed_at: string
  cached: boolean
}

export interface AnalysisState {
  data: AnalyzeResponse | null
  loading: boolean
  error: string | null
}

export function useAnalysis() {
  const config = useRuntimeConfig()
  const state = reactive<AnalysisState>({
    data: null,
    loading: false,
    error: null,
  })

  async function analyzeByUrl(twitterUrl: string): Promise<AnalyzeResponse | null> {
    state.loading = true
    state.error = null
    state.data = null

    try {
      const result = await $fetch<AnalyzeResponse>(
        `${config.public.apiBaseUrl}/api/v1/analyze`,
        {
          method: 'POST',
          body: { url: twitterUrl },
        },
      )
      state.data = result
      return result
    }
    catch (e: unknown) {
      const err = e as { data?: { error?: { message?: string } }; message?: string }
      state.error = err?.data?.error?.message
        || err?.message
        || 'Une erreur est survenue lors de l\'analyse.'
      return null
    }
    finally {
      state.loading = false
    }
  }

  async function analyzeByHandle(handle: string): Promise<AnalyzeResponse | null> {
    return analyzeByUrl(`https://x.com/${handle}`)
  }

  function reset(): void {
    state.data = null
    state.loading = false
    state.error = null
  }

  return {
    state: readonly(state) as Readonly<AnalysisState>,
    analyzeByUrl,
    analyzeByHandle,
    reset,
  }
}
