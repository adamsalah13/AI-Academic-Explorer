def clean_description(description):
    oraciones_filtradas = [o.strip() for o in description if o.strip()]
    resultado = " ".join(oraciones_filtradas)

    return resultado
