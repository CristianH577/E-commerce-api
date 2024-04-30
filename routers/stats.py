from fastapi import APIRouter, HTTPException

import libs.db as db

import pandas as pd

import calendar


# configs ----------------------------------------------------------------------
router = APIRouter(
    prefix="/stats", tags=["stats"], responses={404: {"detail": "no encontrado"}}
)


# functions ----------------------------------------------------------------------
async def productsStats(df: pd.DataFrame, aux: str):
    response = []

    df["quantity"] = df["quantity"].astype(int)
    df["income"] = (df["quantity"] * df["price"]).round(2)

    if aux == "tops":
        df = df.sort_values(by="quantity")
        response.extend(
            [
                {"key": "less", "rows": df.head(3).to_dict(orient="records")},
                {
                    "key": "more",
                    "rows": df.tail(3).iloc[::-1].to_dict(orient="records"),
                },
            ]
        )

        df = df.sort_values(by="income")
        response.extend(
            [
                {"key": "fewest", "rows": df.head(3).to_dict(orient="records")},
                {
                    "key": "most",
                    "rows": df.tail(3).iloc[::-1].to_dict(orient="records"),
                },
            ]
        )

    elif aux == "means":
        quantity_mean = df["quantity"].mean().round(2)
        income_mean = df["income"].mean().round(2)

        response.extend(
            [
                {
                    "key": "means",
                    "rows": [
                        {"of": "Cantidad", "value": quantity_mean},
                        {"of": "Ingreso", "value": "$" + str(income_mean)},
                    ],
                },
            ]
        )

    return response


async def clientsStats(df: pd.DataFrame, aux: str):
    response = []

    df["buys"] = df["buys"].astype(int)
    df["spent"] = df["spent"].round(2)

    if aux == "tops":

        df = df.sort_values(by="buys")
        response.extend(
            [
                {"key": "less", "rows": df.head(3).to_dict(orient="records")},
                {
                    "key": "more",
                    "rows": df.tail(3).iloc[::-1].to_dict(orient="records"),
                },
            ]
        )

        df = df.sort_values(by="spent")
        response.extend(
            [
                {"key": "fewest", "rows": df.head(3).to_dict(orient="records")},
                {
                    "key": "most",
                    "rows": df.tail(3).iloc[::-1].to_dict(orient="records"),
                },
            ]
        )

    elif aux == "means":
        buys_mean = df["buys"].mean().round(2)
        spent_mean = df["spent"].mean().round(2)

        response.extend(
            [
                {
                    "key": "means",
                    "rows": [
                        {"of": "Compra", "value": buys_mean},
                        {"of": "Gasto", "value": "$" + str(spent_mean)},
                    ],
                },
            ]
        )

    return response


async def ticketsStats(df: pd.DataFrame, aux: str):
    response = []

    df["total"] = df["total"].round(2)

    if aux == "tops":
        keys = list(df.head(3))

        df = df.sort_values(by="total")
        less = df.head(3).values.tolist()
        more = df.tail(3).values.tolist()

        response.extend(
            [
                {"key": "less", "rows": [dict(zip(keys, row)) for row in less]},
                {"key": "more", "rows": [dict(zip(keys, row)) for row in more][::-1]},
            ]
        )

    elif aux == "means":
        total_mean = df["total"].mean().round(2)

        response.extend(
            [
                {
                    "key": "means",
                    "rows": [
                        {"of": "Total", "value": total_mean},
                    ],
                },
            ]
        )

    return response


async def sellsStats(df: pd.DataFrame, aux: str):
    response = []

    total = df["frequency"].sum()
    df["frequency"] = (df["frequency"] / total).round(2)

    if aux == "week":
        days_week_names = [
            "lunes",
            "martes",
            "miircoles",
            "jueves",
            "viernes",
            "sabado",
            "domingo",
        ]
        df["time"] = df["time"].apply(lambda x: days_week_names[x - 1])
    if aux == "month":
        df["time"] = df["time"].apply(lambda x: calendar.month_name[x])

    response.extend(
        [
            {"key": "", "rows": df.to_dict(orient="records")},
        ]
    )

    return response


# direcciones --------------------------------------------------------------------------------
@router.get("/")
def index():
    raise HTTPException(status_code=200, detail="stats")


@router.get("/products/{aux}/{aux1}")
async def products(aux: str, aux1: str = None):
    if not aux1:
        aux1 = "tops"

    query = """SELECT S.id_product, SUM(S.quantity) as quantity, 
    P.name_product, P.category_product, P.price 
    FROM sells S
    INNER JOIN products P ON S.id_product = P.id_product
    GROUP BY S.id_product"""
    results = await db.select(query, of="ventas")

    if results:
        df = pd.DataFrame(results)
        response = {}

        if aux == "all":
            response["tables"] = await productsStats(df, aux1)
        elif aux == "category":
            df = df.groupby(by="category_product")

            tabs = []
            for cat, sub_df in df:
                tabs.append({"key": cat, "tables": await productsStats(sub_df, aux1)})

            response["tabs"] = tabs

        return {"value": response}


@router.get("/clients/{aux}/{aux1}")
async def clients(aux: str, aux1: str = None):
    if not aux1:
        aux1 = "tops"

    query = """SELECT T.id_client, COUNT(T.id_client) as buys,
    C.name_client, C.category_client
    FROM tickets T
    INNER JOIN clients C ON T.id_client = C.id_client
    GROUP BY T.id_client"""
    results_tickets = await db.select(query, of="tickets")

    if results_tickets:
        df = pd.DataFrame(results_tickets)

        query = """SELECT S.id_ticket, T.id_client,
        SUM(P.price * S.quantity) as spent
        FROM sells S
        JOIN products P ON S.id_product = P.id_product
        JOIN tickets T ON S.id_ticket = T.id_ticket
        GROUP BY S.id_ticket"""
        results_sells = await db.select(query, of="ventas")

        if results_sells:
            df2 = pd.DataFrame(results_sells)

            spent = df2.groupby("id_client")["spent"].sum().reset_index()
            df = pd.merge(df, spent, on="id_client")

    if isinstance(df, pd.DataFrame):
        response = {}

        if aux == "all":
            response["tables"] = await clientsStats(df, aux1)
        elif aux == "category":
            df = df.groupby(by="category_client")

            tabs = []
            for cat, sub_df in df:
                tabs.append({"key": cat, "tables": await clientsStats(sub_df, aux1)})

            response["tabs"] = tabs

        return {"value": response}


@router.get("/tickets/{aux}")
async def clients(aux: str = None):
    if not aux:
        aux = "tops"

    query = """SELECT S.id_ticket,
        SUM(P.price * S.quantity) as total
        FROM sells S
        JOIN products P ON S.id_product = P.id_product
        JOIN tickets T ON S.id_ticket = T.id_ticket
        GROUP BY S.id_ticket"""
    results = await db.select(query, of="ventas")

    if results:
        df = pd.DataFrame(results)
        response = {}

        response["tables"] = await ticketsStats(df, aux)

        return {"value": response}


@router.get("/sells/{aux}/{aux1}")
async def clients(aux: str, aux1: str = None):
    if not aux1:
        aux1 = "day"

    if aux == "frequency":
        if aux1 == "day":
            # select = "DATE_FORMAT(date, '%H:00')"
            select = "DATE_FORMAT(date, %s)"
            data = ["%H:00"]
        elif aux1 == "week":
            select = "DAYOFWEEK(date)"
        elif aux1 == "month":
            select = "MONTH(date)"
        elif aux1 == "year":
            select = "YEAR(date)"

    if "select" in locals():
        query = f"""SELECT {select} AS time, COUNT(*) AS frequency
        FROM tickets
        GROUP BY time"""

        if "data" in locals():
            data = data
        else:
            data = []

        results = await db.select(query, data=data, of="tickets")

        if results:
            df = pd.DataFrame(results)
            response = {}

            response["tables"] = await sellsStats(df, aux1)

            return {"value": response}
