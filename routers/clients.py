from fastapi import APIRouter, HTTPException, Depends

import os
import json

import libs.db as db
from libs.usefull_functions import getRandomDate
from libs.models import Client


# configs ----------------------------------------------------------------------
router = APIRouter(
    prefix="/clients", tags=["clients"], responses={404: {"detail": "no encontrado"}}
)


# direcciones --------------------------------------------------------------------------------
@router.get("/")
def index():
    raise HTTPException(status_code=200, detail="clients")


@router.post("/add")
async def add(client: Client):
    if not client:
        raise HTTPException(status_code=404, detail="Error de formulario")

    client.date = getRandomDate()

    cols = client.__annotations__.keys()
    values = ["%s"] * len(cols)

    cols = tuple(cols)
    cols = str(cols)
    cols = cols.replace("'", "")

    values = tuple(values)
    values = str(values)
    values = values.replace("'", "")

    query = "INSERT INTO clients " + cols + " VALUES " + values

    data = client.dict().values()
    data = list(data)

    results = await db.insert(query, data=data, of="clientes")

    if results:
        return {"detail": "Agregado"}
    else:
        raise HTTPException(
            status_code=206,
            detail={
                "detail": "No se pudieron guardar los datos",
            },
        )


@router.get("/getAll")
async def getAll():
    query = "SELECT * FROM clients"

    results = await db.select(query, of="clientes")

    if results:
        return {"value": results}


@router.get("/getById/{id}")
async def getById(id: int):
    if not id:
        raise HTTPException(status_code=404, detail="Error de formulario")

    query = f"SELECT * FROM clients WHERE id_client={id}"

    results = await db.select(query, of="clientes")

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
async def delete(id: str):
    if not id:
        raise HTTPException(status_code=404, detail="Error de formulario")

    query = f"DELETE FROM clients WHERE id_client={id}"
    results = await db.delete(query, of="clientes")

    if results:
        return {"detail": "Eliminado"}
    else:
        raise HTTPException(
            status_code=206,
            detail={
                "detail": "No se pudieron eliminar los datos",
            },
        )


@router.put("/update")
async def update(client: Client):
    if not client:
        raise HTTPException(status_code=404, detail="Error de formulario")

    query = "UPDATE clients SET name_client=%s, category_client=%s WHERE id_client=%s"
    data = [
        client.name_client,
        client.category_client,
        client.id_client,
    ]
    results = await db.update(query, data=data, of="clientes")

    if results:
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
    path_file = os.path.join("assets/files", "examples_clients.json")
    if os.path.exists(path_file):
        with open(path_file, "r") as archivo_json:
            data = json.load(archivo_json)

    if data:
        query = f"SELECT id_client FROM clients WHERE name_client='{data[0]['name_client']}'"
        results = await db.select(query, of="clientes")
        if results:
            raise HTTPException(
                status_code=206,
                detail={
                    "detail": "Ejemplos ya agregados",
                },
            )
        else:
            for e in data:
                client = Client(**e)
                await add(client)
            return {"detail": "Clientes de ejemplo agregados"}


@router.get("/getAllIds")
async def getAllIds():
    query = "SELECT id_client FROM clients"
    results = await db.select(query, of="clientes")
    if results:
        ids = []
        for r in results:
            ids.append(r["id_client"])

        return {"value": ids}


