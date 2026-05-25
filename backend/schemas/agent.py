from pydantic import BaseModel, Field
from typing import Annotated, List

class DocSchema(BaseModel):
    title: str
    sections: List[dict] = []

class MindmapSchema(BaseModel):
    title: str
    mermaid_code: str = ""

class QuizItemSchema(BaseModel):
    question: str
    question_type: str  # choice / judgement / short_answer
    options: List[str] = []
    answer: str
    explanation: str = ""

class QuizSchema(BaseModel):
    title: str
    questions: List[dict] = []

class CodeCaseSchema(BaseModel):
    title: str
    description: str = ""
    code: str = ""
    explanation: str = ""

class VideoScriptSchema(BaseModel):
    title: str
    scenes: List[dict] = []
