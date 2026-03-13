import Groq from 'groq-sdk'
import type { ChatCompletionMessageParam, ChatCompletionTool } from 'groq-sdk/resources/chat/completions'
import { getStockQuote, getCompanyProfile } from './finnhubApi'

const client = new Groq({
  apiKey: import.meta.env.VITE_GROQ_API_KEY,
  dangerouslyAllowBrowser: true,
})

const SYSTEM_PROMPT = //Esto permite obtener el contexto del asistente, es decir, que es un asistente de datos financieros y que debe responder en el mismo idioma del usuario.
  'Eres TickerBot, un asistente de datos financieros. Cuando el usuario pregunte sobre una acción o empresa, usa las herramientas disponibles para obtener datos en tiempo real. Responde en el mismo idioma del usuario. Cuando tengas el perfil de la empresa, siempre debes de mencionar en que bolsa cotiza esa empresa y que industria pertenece.'

const tools: ChatCompletionTool[] = [
  {
    type: 'function',
    function: {
      name: 'get_stock_quote',
      description: 'Get the real-time stock quote for a given ticker symbol',
      parameters: {
        type: 'object',
        properties: {
          symbol: {
            type: 'string',
            description: 'The stock ticker symbol, e.g. AAPL, TSLA, MSFT',
          },
        },
        required: ['symbol'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'get_company_profile',
      description: 'Get company profile information for a given ticker symbol',
      parameters: {
        type: 'object',
        properties: {
          symbol: {
            type: 'string',
            description: 'The stock ticker symbol, e.g. AAPL, TSLA, MSFT',
          },
        },
        required: ['symbol'],
      },
    },
  },
]

async function executeTool(name: string, args: { symbol: string }): Promise<string> {
  try {
    if (name === 'get_stock_quote') {
      const quote = await getStockQuote(args.symbol)
      return JSON.stringify(quote)
    } else if (name === 'get_company_profile') {
      const profile = await getCompanyProfile(args.symbol)
      return JSON.stringify(profile)
    }
    throw new Error(`Unknown tool: ${name}`)
  } catch (err) {
    return JSON.stringify({ error: err instanceof Error ? err.message : String(err) })
  }
}

export async function dataAgent(userMessage: string): Promise<string> {
  const messages: ChatCompletionMessageParam[] = [
    { role: 'system', content: SYSTEM_PROMPT },
    { role: 'user', content: userMessage },
  ]

  try {
    // Turn 1: send user message
    const response = await client.chat.completions.create({
      model: 'llama-3.3-70b-versatile',
      messages,
      tools,
      tool_choice: 'auto',
    })

    const assistantMessage = response.choices[0].message

    // No tool calls → return text directly
    if (!assistantMessage.tool_calls || assistantMessage.tool_calls.length === 0) {
      return assistantMessage.content ?? ''
    }

    // Execute all tool calls
    messages.push(assistantMessage)

    for (const toolCall of assistantMessage.tool_calls) {
      const args = JSON.parse(toolCall.function.arguments) as { symbol: string }
      const result = await executeTool(toolCall.function.name, args)
      messages.push({
        role: 'tool',
        tool_call_id: toolCall.id,
        content: result,
      })
    }

    // Turn 2: send tool results back
    const finalResponse = await client.chat.completions.create({
      model: 'llama-3.3-70b-versatile',
      messages,
      tools,
    })

    return finalResponse.choices[0].message.content ?? ''
  } catch (err) {
    console.error('dataAgent error:', err)
    return 'Ocurrió un error al consultar los datos. Intenta de nuevo más tarde.'
  }
}
