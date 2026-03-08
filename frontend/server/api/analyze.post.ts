export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const body = await readBody(event)

  try {
    return await $fetch(`${config.apiInternalUrl}/api/v1/analyze`, {
      method: 'POST',
      body,
    })
  }
  catch (err: any) {
    const status = err?.response?.status ?? 500
    const data = err?.data ?? { error: { message: 'Erreur interne' } }
    throw createError({ statusCode: status, data })
  }
})
