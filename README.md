# TickerBot es un agente de inteligencia artificial que ayuda a personas que no tienen conocimientos profundos en la bolsa de valores. Este agente tiene distintas características que te ayuda a invertir. 
1 - La primera característica es que te proporciona información relacionada sobre la acción que pide el usuario, esta información es el precio actual de bolsa y las ultimas noticias relacionadas sobre la acción. 
<img width="1710" height="952" alt="Captura de pantalla 2026-03-31 a la(s) 10 19 39 a  m" src="https://github.com/user-attachments/assets/136c42e8-5799-4689-8571-6874e0679bd4" />

2 - La segunda característica es que el agente te ayuda a realizar análisis fundamental de la acción que le pidas. Los datos proporcionados son descargados directamente de la SEC-EDGAR. 
<img width="1710" height="827" alt="Captura de pantalla 2026-04-04 a la(s) 6 32 44 p  m" src="https://github.com/user-attachments/assets/3239cfee-81a5-4b25-9ccb-69301848827f" />


3 - La tercera característica es que el agente te proporciona recomendaciones de inversiones de empresas según tu perfil de inversor, tienes dos opciones: Conservador y Agresivo. 
<img width="1698" height="448" alt="Captura de pantalla 2026-03-31 a la(s) 10 25 34 a  m" src="https://github.com/user-attachments/assets/6b98f8ad-5f6f-4562-b0a4-37b6ddf7f370" />
<img width="1709" height="883" alt="Captura de pantalla 2026-03-31 a la(s) 10 26 01 a  m" src="https://github.com/user-attachments/assets/78994cd8-d51d-44c0-bb22-46057e4908b1" />


# Arquitectura del agente 
El agente esta implementado con una arquitectura de multi-agent, ya que tenemos un agente especializado para cada cosa. Un agente especifíco para analizar en tiempo real el precio de la acción. El segundo agente que se especializa en realizar analisis fundamental de empresas, descargando directamente los documentos 10-k de las empresas en el SEC-EDGAR y almacena la información en chunks en chromaDB. El tercer agente que recomienda acciones en base al comportamiento del usuario. 

El stack de este agente fue el siguiente: 
- Lenguajes de programación: React(TypeScript FrontEND), Python(Backend).
- Base de datos: ChromDB para realizar el proceso de RAG, esta base de datos ingesta los datos de 10-k, se realiza el proceso de chunk de los textos con un overlap de 50.  
