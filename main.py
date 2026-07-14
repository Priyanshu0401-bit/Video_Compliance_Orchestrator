"""
Main execution entry
"""

import uuid
import json
import logging
from pprint import pprint

from dotenv import load_dotenv
load_dotenv(override=True)

from backend.src.graph.workflow import app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

logger = logging.getLogger("video_modal_runner")

def run_cli_simulation():
    """
    Simulates video compliance audit request
    """

    session_id = str(uuid.uuid4())
    logger.info(f"Starting video audit simulation with session ID: {session_id}")

    #Define initial state
    initial_state = {
        "video_url" : "",
        "video_id" : f"Vid_{session_id[:8]}",
        "compliance_results" : [],
        "errors" : []
    }

    print("n-----Initializing workfloww")
    print(f"Input payload : {json.dumps(initial_state, indent=2)}")

    try:
        final_state = app.invoke(initial_state)
        print("Workflow is completed")

        print("\n Compliance audit report")
        print(f"video_id : {final_state.get('video_id')}")
        print(f"Status : {final_state.get('final_status')}")
        print("\n [Violations Detected]")
        results = final_state.get("compliance_results",[])
        if results:
            for issue in results:
                print(f"-[{issue.get('severity')} {issue.get('category')} - {issue.get('description')}]-")

    