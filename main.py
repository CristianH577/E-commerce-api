from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware

from routers import products, clients, tickets, sells, stats


#  -----------------------------------------------------------------------------------------
app = FastAPI()
# uvicorn main:app --reload

origins = [
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router)
app.include_router(clients.router)
app.include_router(tickets.router)
app.include_router(sells.router)
app.include_router(stats.router)


# funciones --------------------------------------------------------------------------------


# direcciones --------------------------------------------------------------------------------
@app.get("/")
def index():
    raise HTTPException(status_code=204, detail="funciona")


# # path
# @app.get("/getE/{id}")
# def index(id: int):
#     response = {"error": "execute"}

#     response = search(id)

#     return response


# # query
# @app.get("/getE/")
# async def index(id: int):
#     response = {"error": "execute"}

#     response = search(id)

#     return response
