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


@app.on_event("startup")
async def startup_event():
    print("App is starting up.")
    initialize(dir_path, app)


@app.on_event("shutdown")
def shutdown_event():
    print("App is exiting.", "Wait a moment until completely exits.")
    terminate()
