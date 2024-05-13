from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from fastapi import File, UploadFile, Form

import os
import json
import shutil
from datetime import datetime

import libs.db as db
from libs.usefull_functions import getRandomDate
from libs.models import Product
from routers.history import add as add_history


# configs ----------------------------------------------------------------------
router = APIRouter(
    prefix="/products",
    tags=["products"],
    responses={404: {"detail": "router no encontrado"}},
)


# methods --------------------------------------------------------------------------------
@router.get("/")
async def index():
    raise HTTPException(status_code=200, detail="products")


@router.post("/add")
async def add(product: Product):
    if not product:
        raise HTTPException(status_code=404, detail="Error de formulario")

    product.date = getRandomDate()

    cols = product.__annotations__.keys()
    values = ["%s"] * len(cols)

    cols = tuple(cols)
    cols = str(cols)
    cols = cols.replace("'", "")

    values = tuple(values)
    values = str(values)
    values = values.replace("'", "")

    query = "INSERT INTO products " + cols + " VALUES " + values

    data = product.dict().values()
    data = list(data)

    results = await db.insert(query, data=data, of="productos")

    if results:
        return {"value": results, "detail": "Agregado"}
    else:
        raise HTTPException(
            status_code=206,
            detail={
                "detail": "No se pudieron guardar los datos",
            },
        )


@router.get("/getAll")
async def getAll():
    query = "SELECT * FROM products"
    results = await db.select(query, of="productos")

    if results:
        return {"value": results}


@router.get("/getById/{id}")
async def getById(id: int):
    if not id:
        raise HTTPException(status_code=404, detail="Error de formulario")

    query = "SELECT * FROM products WHERE id_product=%s"
    data = [id]
    results = await db.select(query, data=data, of="productos")

    if results:
        return {"value": results}
    else:
        raise HTTPException(
            status_code=206,
            detail={
                "detail": "No se encontraron resultados",
            },
        )


@router.delete("/delete/{id}")
async def delete(id: int):
    if not id:
        raise HTTPException(status_code=404, detail="Error de formulario")

    # para el historial
    data_old = await getById(id)
    data_old = data_old["value"][0]
    data_old = str(data_old)

    query = f"DELETE FROM products WHERE id_product={id}"
    results = await db.delete(query, of="productos")
    if results:
        await add_history("delete", "products", data_old)
        await deleteImgs(id)
        return {"detail": "Eliminado"}
    else:
        raise HTTPException(
            status_code=206,
            detail={
                "detail": "No se pudieron eliminar los datos",
            },
        )


@router.put("/update")
async def update(product: Product):
    if not product:
        raise HTTPException(status_code=404, detail="Error de formulario")

    # para el historial
    data_old = await getById(product.id_product)
    data_old = data_old["value"][0]
    data_old = str(data_old)

    # agrego el elemento
    product.date = datetime.now()

    cols = product.__annotations__.keys()

    set = ""
    for col in cols:
        if col != "id_product":
            set = set + col + "=%s, "
    set = set[:-2]

    query = "UPDATE products SET " + set + " WHERE id_product=%s"

    data = product.dict().values()
    data = list(data)

    results = await db.update(query, data=data, of="productos")
    if results:
        # si se guardan los datos agrego vieja data al historial
        await add_history("update", "products", data_old)

        return {"detail": "Actualizado"}
    else:
        raise HTTPException(
            status_code=206,
            detail={
                "detail": "No se pudieron actualizar los datos",
            },
        )


@router.get("/addExamples")
async def addExamples():
    data = False
    path_file = os.path.join("assets/files", "examples_products.json")
    if os.path.exists(path_file):
        with open(path_file, "r") as archivo_json:
            data = json.load(archivo_json)

    if data:
        query = f"SELECT id_product FROM products WHERE name_product='{data[0]['name_product']}'"
        results = await db.select(query, of="productos")

        if results:
            raise HTTPException(
                status_code=206,
                detail={
                    "detail": "Ejemplos ya agregados",
                },
            )
        else:
            for e in data:
                product = Product(**e)
                await add(product)

            return {"detail": "Productos de ejemplo agregados"}


@router.get("/getAllIds")
async def getAllIds():
    query = "SELECT id_product FROM products"
    results = await db.select(query, of="productos")

    if results:
        ids = []
        for r in results:
            ids.append(r["id_product"])

        return {"value": ids}


# methods imgs --------------------------------------------------------------------------------
@router.post("/addImgs", status_code=201)
async def addImgs(id: int = Form(...), imgs: list[UploadFile] = File(...)):
    if not (id or imgs):
        raise HTTPException(status_code=404, detail="Error de archivo")

    path_folder = f"assets/imgs/products/{id}"
    start = 0
    if os.path.exists(path_folder) and os.path.isdir(path_folder):
        files = os.listdir(path_folder)
        start = len(files)
    else:
        try:
            os.makedirs(path_folder, exist_ok=True)
        except:
            raise HTTPException(status_code=400, detail="No se crear ruta de archivos")

    errors = 0
    for i, img in enumerate(imgs):
        try:
            file_extension = os.path.splitext(img.filename)[1]
            path_file = f"{path_folder}/{id}_{i+1+start}{file_extension}"
            with open(path_file, "wb") as image:
                image.write(img.file.read())
        except:
            errors += 1

    if errors > 0:
        raise HTTPException(
            status_code=400, detail=f"No se pudieron guardar {errors} imagenes"
        )


@router.post("/getListImgs")
async def getListImgs(ids: list[int] = File(...)):
    if not ids:
        raise HTTPException(status_code=404, detail="Error de formulario")

    results = {}
    for id in ids:
        try:
            folder_name = f"assets/imgs/products/{id}"
            files = os.listdir(folder_name)
            if len(files) > 0:
                results[id] = files
        except:
            False

    return {"value": results}


@router.get("/getImgByName/{id}/{name}")
async def getImgByName(id: int, name: str):
    if not (id or name):
        raise HTTPException(status_code=404, detail="Error de formulario")

    try:
        file_path = f"assets/imgs/products/{id}/{name}"
        if os.path.isfile(file_path):
            return FileResponse(file_path)
    except:
        raise HTTPException(status_code=400, detail="Error al encontrar la imagen")


@router.put("/updateImgs")
async def updateImgs(
    id: int = File(...),
    imgs: list[UploadFile] = File(None),
    toDelete: list[str] = File(None),
):
    if not id:
        raise HTTPException(status_code=404, detail="Error de formulario")

    folder_location = f"assets/imgs/products/{id}"

    if toDelete:
        for delete in toDelete:
            file_location = f"{folder_location}/{delete}"
            if os.path.exists(file_location):
                os.remove(file_location)

        files = os.listdir(folder_location)
        for i, file in enumerate(files):
            ext = os.path.splitext(file)[1]
            new_name = str(id) + "_" + str(i + 1) + ext
            path_old = os.path.join(folder_location, file)
            path_new = os.path.join(folder_location, new_name)
            os.rename(path_old, path_new)

    if imgs:
        await addImgs(id, imgs)


@router.delete("/deleteImgs/{id}")
async def deleteImgs(id: int):
    if not id:
        raise HTTPException(status_code=404, detail="Error de formulario")

    try:
        folder_location = f"assets/imgs/products/{id}"
        if os.path.exists(folder_location) and os.path.isdir(folder_location):
            shutil.rmtree(folder_location)
    except:
        raise HTTPException(
            status_code=400, detail="Error al eliminar imagenes del elemento"
        )
