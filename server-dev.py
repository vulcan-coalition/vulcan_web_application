from fastapi import FastAPI, Depends, HTTPException, Response, Body
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os
import sys
import random
from vulcan_app import *


dir_path = os.path.dirname(os.path.realpath(__file__))

app = FastAPI()

initialize(dir_path, app)


@app.get("/session")
async def get_session(current_user: User = Depends(get_active_current_user)):
    return True


@app.on_event("startup")
async def startup_event():
    print("App is starting up.")
    database.get_session()


@app.on_event("shutdown")
def shutdown_event():
    print("App is exiting.", "Wait a moment until completely exits.")
    terminate()
