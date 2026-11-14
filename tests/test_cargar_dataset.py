from arraigo.pipeline.cargar import construir_colonias, escribir_salidas, validar_anuncios
from arraigo.pipeline.colonias import cargar_catalogo
from arraigo.pipeline.reporte import construir_reporte, escribir_reporte
from arraigo.pipeline.sinteticos import escribir_csv, generar


def test_carga_completa(tmp_path):
    cat = cargar_catalogo()
    raw = tmp_path / "raw"
    escribir_csv(generar(cat, seed=42), raw / "anuncios_sinteticos.csv")
    (raw / "anuncios_malos.csv").write_text(
        "id,operacion,precio_mxn,colonia,alcaldia,recamaras,banos,fuente,fecha_captura\n"
        "m1,renta,0,Roma Norte,Cuauhtémoc,1,1,sintetico,2026-11-14\n"
        "m2,renta,9000,,Cuauhtémoc,1,1,sintetico,2026-11-14\n"
        "m3,renta,9000,Polanco,Miguel Hidalgo,1,1,sintetico,2026-11-14\n", encoding="utf-8")

    validos, rechazados = validar_anuncios(raw, cat)
    escribir_salidas(tmp_path / "out", validos, rechazados, construir_colonias(cat, validos))
    reporte = construir_reporte(validos, rechazados)
    escribir_reporte(tmp_path / "out", reporte)

    assert 200 <= len(validos) <= 500
    assert len(rechazados) == 3
    assert reporte["fraudes_prueba"] >= 15
    assert 10 <= len(reporte["por_colonia"]) <= 15
    assert {i.operacion.value for i in validos} == {"renta", "venta"}
    assert all(i.lat is not None for i in validos)  # los sin coordenadas tomaron el centroide
    for f in ("inmuebles.json", "colonias.json", "rechazados.jsonl", "reporte_calidad.md"):
        assert (tmp_path / "out" / f).exists()
