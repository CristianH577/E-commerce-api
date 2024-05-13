from fastapi import APIRouter, HTTPException

from typing import Dict, List, Union

import libs.db as db
from libs.usefull_functions import getRandomDate
from libs.models import Sell
from routers.sells import addSells


# configs ----------------------------------------------------------------------
router = APIRouter(
    prefix="/tickets", tags=["tickets"], responses={404: {"detail": "no encontrado"}}
)


# direcciones --------------------------------------------------------------------------------
@router.get("/")
def index():
    raise HTTPException(status_code=200, detail="tickets")


@router.post("/add")
async def add(data: Dict[str, Union[int, List[Sell]]]):
    if not (data or data["id_client"] or data["sells"]):
        raise HTTPException(status_code=404, detail="Error de formulario")

    date = getRandomDate()

    query = "INSERT INTO tickets (id_client,date) VALUES (%s,%s)"
    values = [
        data["id_client"],
        date,
    ]
    results = await db.insert(query, values, "tickets")

    if results:
        add_sells = await addSells(results, data["sells"])

        if add_sells:
            raise HTTPException(
                status_code=206,
                detail={
                    "detail": f"No se pudo completar la compra de: {add_sells}. Revise el ticket de la venta.",
                },
            )

        return {"detail": "Agregado"}

    raise HTTPException(
        status_code=400,
        detail="No se pudo guardar el ticket",
    )


@router.get("/getAll")
async def getAll():
    query = "SELECT * FROM tickets"

    results = await db.select(query, of="tickets")

    if results:
        for ticket in results:
            query = f"""SELECT S.id_product, S.quantity, S.subtotal, P.name_product, P.category_product
                FROM sells S
                JOIN products P ON S.id_product=P.id_product
                WHERE S.id_ticket = {ticket['id_ticket']}"""
            sells = await db.select(query, of="ventas")
            if not sells:
                sells = []
            ticket["sells"] = sells

            total = 0
            for sell in sells:
                total = total + sell["subtotal"]
            ticket["total"] = total

        return {"value": results}


@router.get("/getById/{id}")
async def getById(id: int):
    if not id:
        raise HTTPException(status_code=404, detail="Error de formulario")

    query = f"SELECT * FROM tickets WHERE id_ticket={id}"

    results = await db.select(query, of="tickets")

    if results:
        results = results[0]
        query = f"""SELECT S.id_product, S.quantity, P.name_product, P.category_product
            FROM sells S
            JOIN products P ON S.id_product=P.id_product
            WHERE S.id_ticket = {id}"""
        sells = await db.select(query, of="ventas")
        if not sells:
            sells = []
        results["sells"] = sells

        total = 0
        for sell in sells:
            total = total + sell["subtotal"]
        results["total"] = total

        return {"value": results}


@router.delete("/cleanEmptyTickets")
async def cleanEmptyTickets():
    query = "DELETE FROM tickets WHERE id_ticket NOT IN ( SELECT id_ticket FROM sells)"

    results = await db.delete(query, of="tickets")

    if results:
        return {"detail": f"Se eliminaron {results} tickets"}

    raise HTTPException(
        status_code=206,
        detail={
            "detail": "No hay tickets para eliminar",
        },
    )


@router.delete("/deleteAll")
async def deleteAll():
    query = "DELETE FROM tickets"

    results = await db.delete(query, of="tickets")

    if results:
        query = """DELETE FROM sells 
        WHERE id_ticket NOT IN ( SELECT id_ticket FROM tickets )"""
        await db.delete(query, of="ventas")

        return {"detail": f"Se eliminaron {results} tickets"}

    raise HTTPException(
        status_code=206,
        detail={
            "detail": "No hay tickets para eliminar",
        },
    )
