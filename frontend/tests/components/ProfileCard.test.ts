import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ProfileCard from '~/components/ProfileCard.vue'
import type { ProfileSummary } from '~/composables/useAnalysis'

const baseProfile: ProfileSummary = {
  handle: 'testuser',
  display_name: 'Test User',
  bio: 'A test bio',
  followers_count: 1234,
  following_count: 567,
  tweets_count: 8901,
  profile_image_url: 'https://example.com/avatar.jpg',
  account_created_at: '2020-01-01T00:00:00Z',
}

describe('ProfileCard', () => {
  it('renders profile info correctly', () => {
    const wrapper = mount(ProfileCard, { props: { profile: baseProfile } })
    expect(wrapper.text()).toContain('Test User')
    expect(wrapper.text()).toContain('@testuser')
  })

  it('renders avatar image when profile_image_url is set', () => {
    const wrapper = mount(ProfileCard, { props: { profile: baseProfile } })
    const img = wrapper.find('img')
    expect(img.exists()).toBe(true)
    expect(img.attributes('src')).toBe('https://example.com/avatar.jpg')
    expect(img.attributes('referrerpolicy')).toBe('no-referrer')
  })

  it('renders fallback initial when no profile_image_url', () => {
    const profile = { ...baseProfile, profile_image_url: '' }
    const wrapper = mount(ProfileCard, { props: { profile } })
    expect(wrapper.find('img').exists()).toBe(false)
    expect(wrapper.text()).toContain('T')
  })

  it('formats follower count with K suffix', () => {
    const wrapper = mount(ProfileCard, { props: { profile: baseProfile } })
    expect(wrapper.text()).toContain('1.2K')
  })

  it('formats large counts with M suffix', () => {
    const profile = { ...baseProfile, followers_count: 2_500_000 }
    const wrapper = mount(ProfileCard, { props: { profile } })
    expect(wrapper.text()).toContain('2.5M')
  })

  it('displays small numbers as-is', () => {
    const profile = { ...baseProfile, following_count: 42 }
    const wrapper = mount(ProfileCard, { props: { profile } })
    expect(wrapper.text()).toContain('42')
  })
})
