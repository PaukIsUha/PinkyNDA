from fastapi import FastAPI
from router import router as router_main
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

origins = [
    "http://localhost:80",
    "http://0.0.0.0:80"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
    
app.include_router(router_main)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=80)
