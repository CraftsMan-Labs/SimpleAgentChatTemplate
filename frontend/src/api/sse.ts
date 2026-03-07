export async function streamSseData(
  response: Response,
  onData: (payloadText: string) => boolean | void,
): Promise<void> {
  if (!response.body) {
    return
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { value, done } = await reader.read()
    if (done) {
      break
    }

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''

    for (const line of lines) {
      if (!line.startsWith('data: ')) {
        continue
      }
      const shouldStop = onData(line.slice(6).trim())
      if (shouldStop) {
        await reader.cancel()
        return
      }
    }
  }
}
