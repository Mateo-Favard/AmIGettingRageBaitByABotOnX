export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const handle = getRouterParam(event, 'handle')

  try {
    await $fetch(`${config.apiInternalUrl}/api/v1/account/${handle}`, {
      method: 'DELETE',
    })
    setResponseStatus(event, 204)
    return null
  }
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  catch (err: any) {
    const status = err?.response?.status ?? 500
    const data = err?.data ?? { error: { message: 'Erreur interne' } }
    throw createError({ statusCode: status, data })
  }
})
