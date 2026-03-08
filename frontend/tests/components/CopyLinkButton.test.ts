import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import CopyLinkButton from '~/components/CopyLinkButton.vue'

const writeTextMock = vi.fn().mockResolvedValue(undefined)

describe('CopyLinkButton', () => {
  beforeEach(() => {
    writeTextMock.mockClear()
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText: writeTextMock },
      writable: true,
      configurable: true,
    })
    Object.defineProperty(window, 'location', {
      value: { href: 'http://localhost:3000/analysis/testuser' },
      writable: true,
      configurable: true,
    })
  })

  it('renders with default text', () => {
    const wrapper = mount(CopyLinkButton)
    expect(wrapper.text()).toContain('Copier le lien')
  })

  it('copies link on click and shows confirmation', async () => {
    const wrapper = mount(CopyLinkButton)
    await wrapper.find('button').trigger('click')
    await wrapper.vm.$nextTick()

    expect(writeTextMock).toHaveBeenCalledWith(
      'http://localhost:3000/analysis/testuser',
    )
    expect(wrapper.text()).toContain('Lien copié !')
  })

  it('reverts text after 2 seconds', async () => {
    vi.useFakeTimers()
    const wrapper = mount(CopyLinkButton)

    await wrapper.find('button').trigger('click')
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('Lien copié !')

    vi.advanceTimersByTime(2000)
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('Copier le lien')

    vi.useRealTimers()
  })
})
