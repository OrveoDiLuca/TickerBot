import os
from groq import Groq
from services.agent import data_agent, fundamental_agent


client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def classify_mssg(message:str) -> str:
    """Se le va a preguntar a la LLM osea Groq, que tipo de consulta es la que escribió el usuario"""
    response = client.chat.completions.create(
        model = "llama-3.3-70b-versatile",
        messages = [
            {
                "role": "system",
                "content": """Eres un clasificador de intenciones para un bot financiero. Analiza el mensaje del usuario y responde ÚNICAMENTE con una de estas palabras: 
                DATA - si pregunta por precio actual, cotización, noticias, o datos generales de una acción
                FUNDAMENTAL - si pregunta por análisis fundamental, ingresos, deuda, balances, ratios financieros
                RECOMMENDATION - si pide una recomendación de compra, venta o inversión
                UNKNOWN - si no es una consulta financiera sobre acciones

                Responde solo la palabra, sin explicación."""
              },
              {
                  "role": "user",
                  "content": message
              }
        ],
        temperature = 0, #esto significa que le estamos indicando que de respuestas deterministas.
        max_tokens = 10 #Un mensaje corto

    )
    intent = response.choices[0].message.content.strip().upper()
    valid_intents = ["DATA","FUNDAMENTAL","RECOMMENDATION"]
    if intent not in valid_intents:
        return "UNKNOWN"
    return intent

async def orchestrator(message:str): 
    #Por ahora es el unico agente que tenemos programado, entonces se coloca acá. Es el orquestrador más simple, ya que el agente orquestador va a dirigir el mensaje hacia data_agent. 
    intent = classify_mssg(message)  # útil para debuggear
    if intent == "DATA":
        return await data_agent(message)

    elif intent == "FUNDAMENTAL":
        return await fundamental_agent(message)

    #ToDo: agregar el agente de reocomendaciones. 
    elif intent == "RECOMMENDATION":
        # Próximamente: recommendation_agent()
        return await data_agent(message)  # fallback temporal

    else:
        return {
            "reply": "Solo puedo ayudarte con consultas sobre acciones y mercados financieros.",
            "ticker": None,
            "chart": None,
            "news": [],
            "quote": None,
            "name": None,
            "exchange": None,
            "logo": None
          }