from fastapi import FastAPI
from pydantic import BaseModel
from transformers import pipeline

# Inicializamos FastAPI
app = FastAPI()
# Modelo de análisis de sentimientos
sentiment_analyzer = pipeline("sentiment-analysis")
def analizar_sentimiento(request: str):
    result = sentiment_analyzer(request)
    return {"texto": request, "resultado": result}


