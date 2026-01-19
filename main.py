import sqlite3
import struct
import numpy as np
import json
import math
import os
from KKSrag.KKSContentDB import KKSContentDB
from KKSrag.KKStool import KKSTokenizer, FileReader, KKSEmbedding
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from KKSrag.KKSrag import KKSRag
from uuid import uuid4
import asyncio

Tokenizer = KKSTokenizer()
FileReader = FileReader()
Embedding = KKSEmbedding()
config_file = "config/config.json"
with open(config_file, "r") as f:
    config = json.load(f)



class DataInfo(BaseModel):
    filedir: str = ""
    data: list = []
    query: str = ""
    Usembedding: bool = False
    stream: bool = True
    # file: UploadFile = File(...)


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源（开发环境可以用）
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有请求头
)



tasklist = {}

@app.get("/tables")
async def get_tables():
    knowledgelist = []
    dirpath = "db"
    filenames = os.listdir(dirpath)
    for filename in filenames:
        knowledgelist.append((filename.split(".")[0], os.path.join(dirpath, filename)))
    return {"tables": knowledgelist}


@app.post("/get_embedding")
async def get_embedding(request: DataInfo):
    ad = KKSContentDB(Tokenizer, request.filedir)
    return {"data": ad.get_embedding()}


@app.post("/init_embedding")
async def init_embedding(request: DataInfo):
    try:
        global Embedding
        Embedding = KKSEmbedding()
        ad = KKSContentDB(Tokenizer, request.filedir, Embedding)
        ad.init_embedding()
        return {"data": "success"}
    except Exception as e:
        print(e)
        return {"data": "error"}


@app.post("/database")
async def get_database(request: DataInfo):
    if request.Usembedding:
        global Embedding
        ad = KKSContentDB(Tokenizer, request.filedir, Embedding)
    else:
        ad = KKSContentDB(Tokenizer, request.filedir)
    return {"data": ad.select_ad()}


@app.post("/insert")
async def Insert_data(request: DataInfo):
    if request.Usembedding:
        global Embedding
        ad = KKSContentDB(Tokenizer, request.filedir, Embedding)
    else:
        ad = KKSContentDB(Tokenizer, request.filedir)
    try:
        ad.insert_ad(request.data)
        return {"data": "success"}
    except Exception as e:
        print(e)
        return {"data": "error"}


@app.post("/query")
async def Query_data(request: DataInfo):
    if request.Usembedding:
        global Embedding
        ad = KKSContentDB(Tokenizer, request.filedir, Embedding)
    else:
        ad = KKSContentDB(Tokenizer, request.filedir)
    try:
        result = ad.query(request.query)
        print(result)
        return {"data": result}
    except Exception as e:
        print(e)
        return {"data": "error"}


@app.post("/delete")
async def Delete_data(request: DataInfo):
    if request.Usembedding:
        global Embedding
        ad = KKSContentDB(Tokenizer, request.filedir, Embedding)
    else:
        ad = KKSContentDB(Tokenizer, request.filedir)
    try:
        ad.delete_ad(request.data)
        return {"data": "success"}
    except Exception as e:
        print(e)
        return {"data": "error"}


@app.post("/delete_database")
async def Delete_database(request: DataInfo):
    os.remove(request.filedir)
    try:
        return {"data": "success"}
    except:
        return {"data": "error"}


@app.post("/create_database")
async def Create_database(request: DataInfo):
    try:
        file = "db/" + request.filedir + ".db"
        ad = KKSContentDB(Tokenizer, file)
        return {"data": "success"}
    except:
        return {"data": "error"}


@app.post("/rag")
async def Rag_data(request: DataInfo):
    if request.Usembedding:
        global Embedding
        ad = KKSContentDB(Tokenizer, request.filedir, Embedding)
    else:
        ad = KKSContentDB(Tokenizer, request.filedir)
    Rag = KKSRag(
        base_url=config["base_url"],
        model=config["model"],
        api_key=config["api_key"],
    )

    result = ad.query(request.query)
    if len(result) > 5:
        context = "\n".join([item[1] for item in result[:5]])
    else:
        context = "\n".join([item[1] for item in result])

    if request.stream:
        async def generate_text(query, context):
            for char in Rag.Ragresponse(query, context):
                # 2. 只能 yield，不要 return 带值
                yield char.content

        return StreamingResponse(
            generate_text(request.query, context), media_type="text/event-stream"
        )
    else:
        response = Rag.Ragresponse(request.query, context, stream=False)
        return {"data": response.to_json()['kwargs']['content']}
    # return {"data":response}


@app.post("/upload_file")
async def Upload_file(
    file: UploadFile = File(...),
    filedir: str = Form(...),
):
    try:
        contents = await file.read()
        with open("FILE/" + file.filename, "wb") as f:
            f.write(contents)
        data = FileReader.read_excel("FILE/" + file.filename)
        print(data)
        return {"data": data}
    except Exception as e:
        print(e)
        return {"data": "error"}


@app.post("/createtask")
async def Task(request: DataInfo):
    taskid = str(uuid4())
    tasklist[taskid] = request
    return {"taskid": taskid}



@app.get("/stream_query")
async def Stream_query(taskid: str):
    request = tasklist[taskid]
    async def rag_stream(request):
        yield f"data: {json.dumps({'type':'message', 'data':'检索中...'})}\n\n"
        
        if request.Usembedding:
            global Embedding
            ad = KKSContentDB(Tokenizer, request.filedir, Embedding)
        else:
            ad = KKSContentDB(Tokenizer, request.filedir)
        Rag = KKSRag(
            base_url=config["base_url"],
            model=config["model"],
            api_key=config["api_key"],
        )
        result = ad.query(request.query)
        await asyncio.sleep(0.05)  
        if len(result) > 5:
            context = "\n".join([item[1] for item in result[:5]])
        else:
            context = "\n".join([item[1] for item in result])
        
        yield f"data: {json.dumps({'type':'message', 'data':'检索成功'})}\n\n"
        await asyncio.sleep(0.05) 
        yield f"data: {json.dumps({'type':'beginanswer', 'data':'开始回答'})}\n\n"
        for char in Rag.Ragresponse(request.query, context):
                # 2. 只能 yield，不要 return 带值
            yield f"data: {json.dumps({'type': 'answer', 'data': char.content})}\n\n"
            await asyncio.sleep(0.05) 
        yield f"data: {json.dumps({'type':'endanswer', 'data':'回答结束'})}\n\n"
    try:
        return StreamingResponse(
            rag_stream(request), media_type="text/event-stream"
        )
    except Exception as e:
        print(e)
        return {"data": "error"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=12250)

