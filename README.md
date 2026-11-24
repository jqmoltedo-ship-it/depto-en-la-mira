# Buscador diario de departamentos

Combina busquedas publicas de Mercado Libre, ZonaProp y Argenprop, aplica requisitos
excluyentes, agrupa publicaciones de una misma propiedad, guarda un historial en SQLite
y genera un reporte ordenado por oportunidad.

## Criterios actuales

- Hasta USD 200.000.
- Palermo y subzonas, Belgrano y Belgrano R, Nunez, Saavedra, Colegiales o Recoleta.
- 3 ambientes como minimo.
- 80 m2 totales como minimo.
- Una cochera como minimo.
- Dormitorios y m2 cubiertos no son excluyentes: se muestran si el portal los informa, pero no filtran.
- Antiguedad y expensas no excluyen.
- Se favorecen ubicaciones cercanas a Libertador, Santa Fe, Cabildo y el corredor norte.
- Se aceptan propiedades a refaccionar.

Los criterios obligatorios son conservadores: si una publicacion no informa un dato
necesario, queda en `revisar` y no se presenta como coincidencia confirmada.

## Uso

Requiere Python 3.9 o posterior y no instala paquetes ni necesita un token.

```bash
python3 -m real_estate_scraper run
```

El resultado queda en `data/report.html`, `data/matches.csv`, `data/snapshot.csv` y
`data/listings.db`. `snapshot.csv` contiene una fila por propiedad unica, precio anterior,
variacion, `property_key`, fuente elegida, todas las fuentes y todos sus enlaces; es la
fuente usada para el historial de Google Sheets.
Para abrir un conjunto de datos de ejemplo sin acceder a la red:

```bash
python3 -m real_estate_scraper demo
```

Las URL y las opciones se encuentran en `config.toml`. El programa intenta consultar
Mercado Libre directamente; si la pagina de resultados no entrega tarjetas por HTTP,
usa la recoleccion realizada por el navegador normal. La automatizacion abre las tres
busquedas, pagina Mercado Libre hasta el final (con un tope de seguridad de 10 paginas) y genera
`data/browser_sources.json` usando los extractores de `scripts/browser_extract.mjs`.
El comando ignora una exportacion con mas de 30 horas para no mezclar avisos viejos y
descarta avisos promocionados cuyo barrio no esta incluido en la configuracion. Si
Mercado Libre falla o devuelve cero publicaciones, la corrida termina con error antes
de escribir reportes: asi una ejecucion parcial no reemplaza el ultimo Sheet completo.

## Publicaciones duplicadas

El ID del portal identifica un aviso, no una propiedad. El programa mantiene ese ID
junto con su fuente y calcula un `property_key` comun. Solo agrupa automaticamente
avisos de portales distintos cuando coinciden la calle y altura y, ademas, suficientes
caracteristicas estructurales como superficie cubierta, ambientes, dormitorios y precio.
Si ambos avisos informan pisos diferentes, no se agrupan. Dentro de cada grupo se conserva
el menor precio en USD y se publican todos los enlaces originales.

La regla es deliberadamente conservadora: es preferible dejar dos filas para revisar que
unir departamentos diferentes del mismo edificio.

## Ejecucion cada 2 dias en macOS, publicada en GitHub Pages

El job corre `scripts/run_and_publish.sh`, que ejecuta el buscador y, si
`data/report.html` cambio, copia el resultado a `docs/index.html`, hace commit y
`git push` a `main` usando una deploy key dedicada (`~/.ssh/id_ed25519_depto_scraper`).
GitHub Pages sirve ese archivo desde `main` / carpeta `/docs`, asi que el link publico
se actualiza solo en cada corrida.

Primero ejecutar manualmente (`./scripts/run_and_publish.sh`) y comprobar el reporte en
`docs/index.html` y en el link de Pages. Luego instalar el job, pasando la cantidad de
dias entre corridas (por defecto, 2):

```bash
./scripts/install_launchd.sh 2
```

El job corre una vez al instalarse (`RunAtLoad`) y despues cada `N` dias mientras la
Mac este encendida; si estaba apagada o dormida al vencer el intervalo, `launchd` lo
ejecuta en cuanto vuelve a estar disponible. Los logs quedan en `data/job.log` y
`data/job-error.log`.

Para quitarlo:

```bash
launchctl bootout "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.local.departamentos.plist"
rm "$HOME/Library/LaunchAgents/com.local.departamentos.plist"
```

ZonaProp y Argenprop son fuentes opcionales: solo se incluyen si existe una
exportacion reciente (menor a 30 horas) en `data/browser_sources.json`, generada a mano
o con una automatizacion de navegador aparte. Sin esa exportacion, el job corre
igual usando solo Mercado Libre.

## Como se calcula la oportunidad

Primero se filtran los requisitos obligatorios. Para los resultados restantes se
calcula USD/m2 cubierto y se compara con la mediana del mismo barrio obtenida en esa
corrida. El puntaje combina el descuento frente a esa mediana, la cercania textual
o geografica al corredor preferido y una pequena bonificacion por `a refaccionar`.
Una mediana calculada con pocas propiedades se muestra como orientativa.

El HTML y los campos publicados por vendedores pueden cambiar o contener errores.
El reporte ayuda a encontrar candidatos; siempre hay que verificar precio, titulo,
documentacion y cochera en la publicacion original antes de tomar una decision.
