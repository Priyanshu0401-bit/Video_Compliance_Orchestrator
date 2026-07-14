from pydantic import BaseModel,Field
import operator
from typing import List,TypedDict,Annotated,Dict,Optional,Any

#define schema for single compliance result
class ComplianceIssue(TypedDict):
    category: str
    description: str #specific detail of violation
    severity: str
    timestamp: Optional[str]

#global graph state
class VideoAuditState(TypedDict):
    '''
    Defines the data schema for langgraph execution content
    Main container: holds all info about the audit with initial url and final report
    '''

    video_url: str
    video_id: str

    #ingestion and extraction data
    local_file_path : Optional[str]
    video_metadata: Dict[str,Any]
    transcript: Optional[str]
    ocr_text: List[str]

    #analysis output
    compliance_results: Annotated[List[ComplianceIssue], operator.add]

    #final deliverables
    final_status: str
    final_report: str

    #system observability
    errors:Annotated[List[str], operator.add]