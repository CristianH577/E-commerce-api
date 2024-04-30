from fastapi import HTTPException

import MySQLdb
import locale


db_config = {
    "host": "localhost",
    "user": "root",
    "passwd": "",
    "db": "ecommerce",
}

locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")


def connect_db():
    try:
        conn = MySQLdb.connect(**db_config)
        return conn
    except MySQLdb.Error:
        raise HTTPException(
            status_code=400, detail="Error al conectar a la base de datos"
        )


def get_db_conn():
    conn = connect_db()
    try:
        yield conn
    finally:
        conn.close()


async def select(
    query: str, data: list = [], of: str = None, conn: MySQLdb.Connection = connect_db()
):
    try:
        cursor = conn.cursor()
        cursor.execute(query, data)
        results = cursor.fetchall()

        if results:
            keys = [desc[0] for desc in cursor.description]
            results_list = [dict(zip(keys, row)) for row in results]
            return results_list

    except:
        msg = "Error al obtener datos"
        if of:
            msg += f": {of}"
        raise HTTPException(status_code=400, detail=msg)

    finally:
        cursor.close()

    return False


async def insert(
    query: str, data: list = [], of: str = None, conn: MySQLdb.Connection = connect_db()
):
    try:
        cursor = conn.cursor()
        cursor.execute(query, data)
        conn.commit()

        if cursor.rowcount > 0:
            return cursor.lastrowid

    except:
        msg = "Error al guardar datos"
        if of:
            msg += f": {of}"
        raise HTTPException(status_code=400, detail=msg)

    finally:
        cursor.close()

    return False


async def delete(
    query: str, data: list = [], of: str = None, conn: MySQLdb.Connection = connect_db()
):
    try:
        cursor = conn.cursor()
        cursor.execute(query, data)
        conn.commit()

        if cursor.rowcount > 0:
            return cursor.rowcount

    except:
        msg = "Error al eliminar datos"
        if of:
            msg += f": {of}"
        raise HTTPException(status_code=400, detail=msg)

    finally:
        cursor.close()

    return False


async def update(
    query: str, data: list = [], of: str = None, conn: MySQLdb.Connection = connect_db()
):
    try:
        cursor = conn.cursor()
        cursor.execute(query, data)
        conn.commit()

        if cursor.rowcount > 0:
            return cursor.rowcount

    except:
        msg = "Error al actualizar datos"
        if of:
            msg += f": {of}"
        raise HTTPException(status_code=400, detail=msg)

    finally:
        cursor.close()

    return False
