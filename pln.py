"""Procesamiento de Lenguaje Natural (PLN) básico con NLTK.

Técnicas que se aplican a cada mensaje del estudiante:
  1. Normalización      -> minúsculas y sin acentos
  2. Tokenización       -> NLTK RegexpTokenizer
  3. Palabras vacías    -> lista de stopwords en español de NLTK
  4. Corrección         -> errores de escritura (difflib)
  5. Raíces (stemming)  -> NLTK SnowballStemmer en español
"""
import difflib
import unicodedata

from nltk.stem import SnowballStemmer
from nltk.tokenize import RegexpTokenizer

_tokenizador = RegexpTokenizer(r"\w+")
_stemmer = SnowballStemmer("spanish")

# Se usa solo si no se pueden descargar las stopwords de NLTK (por ejemplo, sin internet).
PALABRAS_VACIAS_RESPALDO = """
de la que el en y a los del se las por un para con no una su al lo como mas pero sus le ya o
este si porque esta entre cuando muy sin sobre tambien me hasta hay donde quien desde todo nos
durante todos uno les ni contra otros ese eso ante ellos e esto mi antes algunos unos yo otro
otras otra tanto esa estos mucho quienes nada muchos cual poco ella estar estas algunas algo
nosotros mis tu te ti tus ellas es son soy eres somos fue era ser sea estoy esta estan estamos
tengo tiene tienes tienen tenemos he has ha han hemos
""".split()

# Palabras que NLTK considera vacías pero que el chatbot necesita ("¿quién imparte...?").
CONSERVAR = {"quien", "quienes", "cual", "cuando", "donde"}


def normalizar(texto):
    """Minúsculas y sin acentos: 'HORARIOS' -> 'horarios', 'Cálculo' -> 'calculo'."""
    texto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def _cargar_palabras_vacias():
    try:
        from nltk.corpus import stopwords
        try:
            lista = stopwords.words("spanish")
        except LookupError:
            import nltk
            nltk.download("stopwords", quiet=True)
            lista = stopwords.words("spanish")
        print("PLN: palabras vacías cargadas desde NLTK.")
    except Exception:
        lista = PALABRAS_VACIAS_RESPALDO
        print("PLN: no se pudo cargar NLTK stopwords; se usa la lista de respaldo.")
    return {normalizar(p) for p in lista}


PALABRAS_VACIAS = _cargar_palabras_vacias()


def tokenizar(texto_normalizado):
    return _tokenizador.tokenize(texto_normalizado)


def quitar_vacias(tokens):
    return [t for t in tokens if t not in PALABRAS_VACIAS or t in CONSERVAR]


def raiz(palabra):
    return _stemmer.stem(palabra)


def corregir(tokens, vocabulario):
    """Corrige errores de escritura parecidos a una palabra conocida ('horaro' -> 'horario')."""
    resultado = []
    for t in tokens:
        if len(t) < 5 or t in vocabulario or any(c.isdigit() for c in t):
            resultado.append(t)
            continue
        parecidas = difflib.get_close_matches(t, vocabulario, n=1, cutoff=0.82)
        resultado.append(parecidas[0] if parecidas else t)
    return resultado


def procesar(texto, vocabulario):
    normalizado = normalizar(texto)
    tokens = tokenizar(normalizado)
    sin_vacias = quitar_vacias(tokens)
    corregidos = corregir(sin_vacias, vocabulario)
    return {
        "normalizado": normalizado,
        "tokens": tokens,
        "sin_vacias": sin_vacias,
        "corregidos": corregidos,
        "raices": {raiz(t) for t in corregidos},
    }