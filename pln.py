import re
import unicodedata
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


FAQ = [
    {
        "pregunta": "¿Cuándo empiezan las inscripciones?",
        "respuesta": "Consulta el calendario académico oficial para conocer las fechas de inscripción.",
        "categoria": "Inscripciones",
    },
    {
        "pregunta": "¿Dónde puedo consultar mi horario?",
        "respuesta": "Consulta tus horarios en el portal escolar de tu universidad.",
        "categoria": "Horarios",
    },
    {
        "pregunta": "¿Quién es mi profesor de cálculo?",
        "respuesta": "Consulta el catálogo docente o tu horario para identificar a tu profesor.",
        "categoria": "Profesores",
    },
    {
        "pregunta": "¿Cómo puedo solicitar una constancia?",
        "respuesta": "Consulta los requisitos de servicios escolares de tu universidad.",
        "categoria": "Trámites",
    },
    {
        "pregunta": "¿Dónde consulto las materias de mi carrera?",
        "respuesta": "Revisa el plan de estudios oficial de tu carrera.",
        "categoria": "Materias",
    },
]


def normalizar(texto):
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(
        c for c in texto
        if unicodedata.category(c) != "Mn"
    )
    texto = re.sub(r"[^\w\s]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


vectorizador = TfidfVectorizer(ngram_range=(1, 2))

preguntas = [
    normalizar(item["pregunta"])
    for item in FAQ
]

matriz_faq = vectorizador.fit_transform(preguntas)


def responder(mensaje, umbral=0.20):
    mensaje = normalizar(mensaje)

    if not mensaje:
        return {
            "respuesta": "Escribe una pregunta para comenzar.",
            "categoria": "General",
            "confianza": 0.0,
            "resuelta": False,
        }

    vector = vectorizador.transform([mensaje])
    similitudes = cosine_similarity(
        vector, matriz_faq
    ).flatten()

    mejor_indice = similitudes.argmax()
    confianza = float(similitudes[mejor_indice])

    if confianza < umbral:
        return {
            "respuesta": (
                "No encontré información suficiente. "
                "Intenta reformular tu pregunta o consulta "
                "a servicios escolares."
            ),
            "categoria": "Sin respuesta",
            "confianza": confianza,
            "resuelta": False,
        }

    item = FAQ[mejor_indice]

    return {
        "respuesta": item["respuesta"],
        "categoria": item["categoria"],
        "confianza": confianza,
        "resuelta": True,
    }