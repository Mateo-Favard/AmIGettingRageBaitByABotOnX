import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ScoreBar from '~/components/ScoreBar.vue'

describe('ScoreBar', () => {
  it('renders green bar for score < 30', () => {
    const wrapper = mount(ScoreBar, { props: { score: 15, label: 'Test' } })
    const bar = wrapper.find('.rounded-full.transition-all')
    expect(bar.classes()).toContain('bg-green-500')
    expect(wrapper.text()).toContain('15/100')
  })

  it('renders yellow bar for score between 30 and 60', () => {
    const wrapper = mount(ScoreBar, { props: { score: 45, label: 'Test' } })
    const bar = wrapper.find('.rounded-full.transition-all')
    expect(bar.classes()).toContain('bg-yellow-500')
    expect(wrapper.text()).toContain('45/100')
  })

  it('renders red bar for score >= 60', () => {
    const wrapper = mount(ScoreBar, { props: { score: 80, label: 'Test' } })
    const bar = wrapper.find('.rounded-full.transition-all')
    expect(bar.classes()).toContain('bg-red-500')
    expect(wrapper.text()).toContain('80/100')
  })

  it('renders N/A for null score', () => {
    const wrapper = mount(ScoreBar, { props: { score: null, label: 'Test' } })
    expect(wrapper.text()).toContain('N/A')
    const bar = wrapper.find('.rounded-full.transition-all')
    expect(bar.classes()).toContain('bg-zinc-600')
  })

  it('clamps score above 100', () => {
    const wrapper = mount(ScoreBar, { props: { score: 150 } })
    const bar = wrapper.find('.rounded-full.transition-all')
    expect(bar.attributes('style')).toContain('width: 100%')
  })

  it('clamps score below 0', () => {
    const wrapper = mount(ScoreBar, { props: { score: -10 } })
    const bar = wrapper.find('.rounded-full.transition-all')
    expect(bar.attributes('style')).toContain('width: 0%')
  })

  it('does not show label when not provided', () => {
    const wrapper = mount(ScoreBar, { props: { score: 50 } })
    expect(wrapper.find('.text-sm.text-zinc-400').exists()).toBe(false)
  })

  it('uses larger height when large prop is true', () => {
    const wrapper = mount(ScoreBar, { props: { score: 50, large: true } })
    const track = wrapper.find('.bg-zinc-700')
    expect(track.classes()).toContain('h-3')
  })

  it('uses smaller height by default', () => {
    const wrapper = mount(ScoreBar, { props: { score: 50 } })
    const track = wrapper.find('.bg-zinc-700')
    expect(track.classes()).toContain('h-2')
  })
})
