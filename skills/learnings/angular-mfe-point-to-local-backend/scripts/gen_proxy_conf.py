"""Genera proxy.conf.json para apuntar un front Angular a MS locales.
Cada entrada reescribe un segmento de path a su puerto+context-path local.
Edita MAPPINGS con tus (segmento, puerto, context_path) y corre el script
en la raiz del repo del frontend. Revisa el archivo antes de usarlo.
"""
import json
import os

# (segmento que arma el front, puerto local del MS, context-path real del MS)
MAPPINGS = [
    ("autorizacion-salud", 8080, "gb-autorizacion-salud"),
    ("autorizacion-arl", 8087, "gb-autorizacion-arl"),
    ("procesos-masivos-salud", 8088, "gb-procesos-masivos-salud"),
]

OUT = "proxy.conf.json"


def build():
    conf = {
        "_comment": "LOCAL ONLY - reparte cada segmento a su MS local. NO COMMITEAR.",
    }
    for seg, port, ctx in MAPPINGS:
        key = "/" + seg
        conf[key] = {
            "target": "http://localhost:%d" % port,
            "pathRewrite": {"^/" + seg: "/" + ctx},
            "secure": False,
            "changeOrigin": True,
            "logLevel": "debug",
        }
    return conf


def main():
    if os.path.exists(OUT):
        print("AVISO: %s ya existe; se sobrescribira." % OUT)
    data = build()
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    segs = [k for k in data if not k.startswith("_")]
    print("Escrito %s con %d entradas: %s" % (OUT, len(segs), ", ".join(segs)))
    print("Recuerda: declara proxyConfig en angular.json (no --proxy-config CLI).")


if __name__ == "__main__":
    main()
