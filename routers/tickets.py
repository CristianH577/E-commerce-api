from fastapi import APIRouter, HTTPException

import libs.db as db
from libs.usefull_functions import getRandomDate
from libs.models import Ticket


# configs ----------------------------------------------------------------------
router = APIRouter(
    prefix="/tickets", tags=["tickets"], responses={404: {"detail": "no encontrado"}}
)


# direcciones --------------------------------------------------------------------------------
@router.get("/")
def index():
    raise HTTPException(status_code=200, detail="tickets")


@router.post("/add")
async def add(ticket: Ticket):
    if not ticket:
        raise HTTPException(status_code=404, detail="Error de formulario")

    date = getRandomDate()

    query = "INSERT INTO tickets (id_client,date) VALUES (%s,%s)"
    data = [
        ticket.id_client,
        date,
    ]
    results = await db.insert(query, data=data, of="tickets")

    if results:
        return {"value": results}
    else:
        raise HTTPException(
            status_code=206,
            detail={
                "detail": "No se pudieron guardar los datos",
            },
        )


@router.get("/getAll")
async def getAll():
    query = "SELECT * FROM tickets"

    results = await db.select(query, of="tickets")

    if results:
        for ticket in results:
            query = f"""SELECT S.id_product, S.quantity, P.name_product, P.category_product
                FROM sells S
                JOIN products P ON S.id_product=P.id_product
                WHERE S.id_ticket = {ticket['id_ticket']}"""
            sells = await db.select(query, of="ventas")
            if not sells:
                sells = []
            ticket["sells"] = sells

        return {"value": results}


@router.get("/getById/{id}")
async def getById(id: str):
    if not id:
        raise HTTPException(status_code=404, detail="Error de formulario")

    query = f"SELECT * FROM tickets WHERE id_ticket={id}"

    results = await db.select(query, of="tickets")

    if results:
        query = f"""SELECT S.id_product, S.quantity, P.name_product, P.category_product
            FROM sells S
            JOIN products P ON S.id_product=P.id_product
            WHERE S.id_ticket = {id}"""
        sells = await db.select(query, of="ventas")
        if not sells:
            sells = []
        results[0]["sells"] = sells

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
