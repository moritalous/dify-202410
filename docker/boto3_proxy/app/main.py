import boto3
from fastapi import FastAPI, status
from pydantic import BaseModel
from fastapi.responses import JSONResponse

app = FastAPI(servers=[{"url": "http://boto3proxy:8000"}])


class Input(BaseModel):
    service: str
    region: str
    method: str
    params: dict


@app.post("/aws", summary="Call AWS API")
def aws_api(input: Input):

    try:

        service_name = input.service
        region_name = input.region
        func_name = input.method
        params = input.params

        client = boto3.client(service_name, region_name=region_name)
        method = getattr(client, func_name)
        response = method(**params)

        return response

    except Exception as e:
        return JSONResponse(content=str(e), status_code=status.HTTP_400_BAD_REQUEST)


@app.post("/credentials", summary="Get AWS credentials")
def credentials():

    try:

        client = boto3.Session().get_credentials().get_frozen_credentials()
        return client

    except Exception as e:
        return JSONResponse(content=str(e), status_code=status.HTTP_400_BAD_REQUEST)

