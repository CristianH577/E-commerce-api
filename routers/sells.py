from fastapi import APIRouter, HTTPException

from typing import List

import libs.db as db
from libs.models import Sell


# configs ----------------------------------------------------------------------
router = APIRouter(
    prefix="/sells", tags=["sells"], responses={404: {"detail": "no encontrado"}}
)


# functions --------------------------------------------------------------------------------
async def updateStock(sell: Sell, allow_raise: bool = False):
    query = "UPDATE products SET stock = stock - %s WHERE id_product=%s"
    data = [sell.quantity, sell.id_product]
    of = "productos"

    return await db.update(query, data, of, allow_raise)


async def addSell(sell: Sell, allow_raise: bool = False):
    query = "INSERT INTO sells (id_ticket,id_product,quantity, subtotal) VALUES (%s,%s,%s,%s)"
    data = [
        sell.id_ticket,
        sell.id_product,
        sell.quantity,
        sell.subtotal,
    ]

    return await db.insert(query, data, "ventas", allow_raise)


# direcciones --------------------------------------------------------------------------------
@router.get("/")
def index():
    raise HTTPException(status_code=200, detail="sells")


# @router.post("/add")
# async def add(sell: Sell):
#     if not sell:
#         raise HTTPException(status_code=404, detail="Error de formulario")

#     # actualizo stock
#     update_stock = await updateStock(sell)
#     if not update_stock:
#         raise HTTPException(
#             status_code=206, detail={"detail": "No se pudo actualizar actualizar stock"}
#         )
#     else:
#         # guardo la venta
#         add_sell = await addSell(sell)

#         if not add_sell:
#             sell.quantity = sell.quantity * -1
#             await updateStock(sell)

#             raise HTTPException(
#                 status_code=400,
#                 detail="No se pudo guardar la venta",
#             )


@router.post("/addSells")
async def addSells(id_ticket: int, sells: List[Sell]):
    if not (id_ticket or sells):
        raise HTTPException(status_code=404, detail="Error de formulario")

    names = []
    errors = []

    for sell in sells:
        update_stock = await updateStock(sell)
        if update_stock:
            sell.id_ticket = id_ticket
            add_sell = await addSell(sell)
            if not add_sell:
                sell.quantity = sell.quantity * -1
                await updateStock(sell)

        if not (update_stock or add_sell):
            errors.append(sell.id_product)
            names.append(sell.name_product)

    if errors or names:
        # si son muchos
        if len(names) > 5:
            names = names[0:4]
            names.append("...")

        msg = ", ".join(names)
        return msg

    return False


@router.get("/getAll")
async def getAll():
    query = "SELECT S.*, P.name_product, P.category_product FROM sells S JOIN products P ON S.id_product=P.id_product"

    results = await db.select(query, of="ventas")

    if results:
        return {"value": results}


@router.get("/getById/{id}")
async def getById(id: int):
    if not id:
        raise HTTPException(status_code=404, detail="Error de formulario")

    query = f"""SELECT S.*, P.name_product, P.category_product 
        FROM sells S 
        JOIN products P ON S.id_product=P.id_product 
        WHERE S.id_product={id}"""

    results = await db.select(query, of="ventas")

    if results:
        return {"value": results}


@router.post("/checkSells")
async def checkSells(sells: List[Sell]):
    if not sells:
        raise HTTPException(status_code=404, detail="Error de formulario")

    names = []
    errors = []

    for sell in sells:
        query = "SELECT id_product FROM products WHERE id_product = %s AND stock >= %s"
        data = [
            sell.id_product,
            sell.quantity,
        ]

        results = await db.select(query, data, "productos", False)
        if not results:
            errors.append(sell.id_product)
            names.append(sell.name_product)

    if errors or names:
        # si son muchos
        if len(names) > 5:
            names = names[0:4]
            names.append("...")

        msg = ", ".join(names)
        raise HTTPException(
            status_code=206,
            detail={
                "value": errors,
                "detail": f"No hay suficiente stock de: {msg}",
            },
        )


@router.delete("/cleanUnknownSells")
async def cleanUnknownSells():
    query = """DELETE FROM sells 
        WHERE id_ticket NOT IN ( SELECT id_ticket FROM tickets ) 
        OR id_product NOT IN ( SELECT id_product FROM tickets )"""
    results = await db.delete(query, of="ventas")

    if results:
        return {"detail": f"Se eliminaron {results} ventas"}

    raise HTTPException(
        status_code=206,
        detail={
            "detail": "No hay ventas para eliminar",
        },
    )
