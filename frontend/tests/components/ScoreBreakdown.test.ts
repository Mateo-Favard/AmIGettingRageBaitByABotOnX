import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ScoreBreakdown from '~/components/ScoreBreakdown.vue'
import ScoreBar from '~/components/ScoreBar.vue'
import type { ScoreBreakdown as ScoreBreakdownType } from '~/composables/useAnalysis'

const scores: ScoreBreakdownType = {
  ai_content_score: 85,
  behavioral_score: 42,
  sentiment_score: 15,
  political_shift_score: 70,
  network_score: null,
}

describe('ScoreBreakdown', () => {
  it('renders 5 ScoreBar components', () => {
    const wrapper = mount(ScoreBreakdown, {
      props: { scores },
      global: { components: { ScoreBar } },
    })
    const bars = wrapper.findAllComponents(ScoreBar)
    expect(bars).toHaveLength(5)
  })

  it('renders French labels', () => {
    const wrapper = mount(ScoreBreakdown, {
      props: { scores },
      global: { components: { ScoreBar } },
    })
    const text = wrapper.text()
    expect(text).toContain('Contenu IA')
    expect(text).toContain('Comportement')
    expect(text).toContain('Sentiment')
    expect(text).toContain('Virage politique')
    expect(text).toContain('Réseau')
  })

  it('passes correct scores to ScoreBar components', () => {
    const wrapper = mount(ScoreBreakdown, {
      props: { scores },
      global: { components: { ScoreBar } },
    })
    const bars = wrapper.findAllComponents(ScoreBar)
    expect(bars[0].props('score')).toBe(85)
    expect(bars[1].props('score')).toBe(42)
    expect(bars[2].props('score')).toBe(15)
    expect(bars[3].props('score')).toBe(70)
    expect(bars[4].props('score')).toBeNull()
  })

  it('renders section title', () => {
    const wrapper = mount(ScoreBreakdown, {
      props: { scores },
      global: { components: { ScoreBar } },
    })
    expect(wrapper.text()).toContain('Détail des signaux')
  })
})
