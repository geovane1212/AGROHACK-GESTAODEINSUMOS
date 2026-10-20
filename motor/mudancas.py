"""'O que mudou' entre duas análises: alertas novos, resolvidos e que mudaram de severidade."""

from .alertas import ORDEM_SEVERIDADE


def fotografar(alertas) -> dict:
    """Versão enxuta dos alertas, para guardar no banco e comparar depois."""
    return {a.chave: {"titulo": a.titulo, "produto": a.produto, "severidade": a.severidade}
            for a in alertas}


def comparar(antes: dict, depois: dict) -> dict:
    novos = [depois[k] for k in depois.keys() - antes.keys()]
    resolvidos = [antes[k] for k in antes.keys() - depois.keys()]
    mudaram = []
    for k in antes.keys() & depois.keys():
        de, para = antes[k]["severidade"], depois[k]["severidade"]
        if de != para:
            mudaram.append({**depois[k], "de": de, "para": para,
                            "piorou": ORDEM_SEVERIDADE[para] < ORDEM_SEVERIDADE[de]})
    ordem = lambda x: (ORDEM_SEVERIDADE[x["severidade"]], x["produto"])  # noqa: E731
    return {"novos": sorted(novos, key=ordem), "resolvidos": sorted(resolvidos, key=ordem),
            "mudaram": sorted(mudaram, key=ordem)}
