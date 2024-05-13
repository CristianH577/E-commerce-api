from fastapi import APIRouter, HTTPException

from datetime import datetime

import libs.db as db
from libs.models import History


# configs ----------------------------------------------------------------------
router = APIRouter(
    prefix="/history", tags=["history"], responses={404: {"detail": "no encontrado"}}
)


# direcciones --------------------------------------------------------------------------------
@router.get("/")
def index():
    raise HTTPException(status_code=200, detail="history")


@router.post("/add")
async def add(action: str, table: str, data: str):
    if not (action or table or data):
        raise HTTPException(status_code=404, detail="Error de formulario")

    history = History(action=action, table_name=table, data_element=data)
    history.date = datetime.now()
    # history.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cols = history.__annotations__.keys()
    values = ["%s"] * len(cols)

    cols = tuple(cols)
    cols = str(cols)
    cols = cols.replace("'", "")

    values = tuple(values)
    values = str(values)
    values = values.replace("'", "")

    query = "INSERT INTO history_changes " + cols + " VALUES " + values

    data = history.dict().values()
    data = list(data)

    results = await db.insert(query, data=data, of="historial de cambios")

    if results:
        return {"detail": "Agregado"}
    else:
        raise HTTPException(
            status_code=206,
            detail={
                "detail": "No se pudieron guardar los datos de historial",
            },
        )


@router.get("/getAll")
async def getAll():
    query = "SELECT * FROM history_changes"

    results = await db.select(query, of="historial de cambios")

    if results:
        return {"value": results}

