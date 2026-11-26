def semestres_ofertados(tipo_periodo: str) -> list[int]:
    """ENERO_JUNIO -> pares. AGOSTO_DICIEMBRE -> impares."""
    if tipo_periodo == "ENERO_JUNIO":
        return [2, 4, 6, 8, 10]
    if tipo_periodo == "AGOSTO_DICIEMBRE":
        return [1, 3, 5, 7, 9]
    return []