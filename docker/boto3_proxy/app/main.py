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
        response = boto3.Session().get_credentials().get_frozen_credentials()

        return {
            "access_key": response.access_key,
            "secret_key": response.secret_key,
            "token": response.token,
        }

    except Exception as e:
        return JSONResponse(content=str(e), status_code=status.HTTP_400_BAD_REQUEST)


## Bedrock Knowledge Bases


class RetrievalSetting(BaseModel):
    top_k: int
    score_threshold: float


class RetrievalParams(BaseModel):
    knowledge_id: str
    query: str
    retrieval_setting: RetrievalSetting


@app.post("/retrieval", summary="Retrieve from Bedrock Knowledge Bases")
def aws_api(input: RetrievalParams):

    try:

        client = boto3.client("bedrock-agent-runtime", region_name="us-east-1")
        response = client.retrieve(
            knowledgeBaseId=input.knowledge_id,
            retrievalQuery=input.query,
            retrievalConfiguration={
                "vectorSearchConfiguration": {
                    "numberOfResults": input.retrieval_setting.top_k
                }
            },
        )

        retrieval_results = response["retrievalResults"]

        records = [
            {
                "content": result["content"]["text"],
                "score": result["score"],
                "title": result["location"]["s3Location"]["uri"],
                "metadata": result["metadata"],
            }
            for result in retrieval_results
        ]

        return {"records": records}

    except Exception as e:
        return JSONResponse(content=str(e), status_code=status.HTTP_400_BAD_REQUEST)
