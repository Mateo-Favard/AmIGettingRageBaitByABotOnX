import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import AnalysisSkeleton from '~/components/AnalysisSkeleton.vue'

describe('AnalysisSkeleton', () => {
  it('renders without errors', () => {
    const wrapper = mount(AnalysisSkeleton)
    expect(wrapper.exists()).toBe(true)
  })

  it('has animate-pulse class', () => {
    const wrapper = mount(AnalysisSkeleton)
    expect(wrapper.find('.animate-pulse').exists()).toBe(true)
  })

  it('renders skeleton blocks for profile, score, and breakdown', () => {
    const wrapper = mount(AnalysisSkeleton)
    // Profile skeleton (avatar circle)
    expect(wrapper.find('.rounded-full').exists()).toBe(true)
    // Score bar skeleton (full-width rounded bar)
    expect(wrapper.find('.rounded-full.w-full').exists()).toBe(true)
    // Multiple skeleton blocks for breakdown
    const skeletonBlocks = wrapper.findAll('.bg-zinc-700')
    expect(skeletonBlocks.length).toBeGreaterThan(5)
  })
})
