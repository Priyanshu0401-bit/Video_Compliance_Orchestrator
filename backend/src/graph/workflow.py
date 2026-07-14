'''
This modeule defines the DAG: Directed Acyclic Graph
Defines the overall orchestration of the compliances nodes

START -> index_video_node -> audit_content_node -> END
'''

from langgraph.graph import StateGraph, END
from backend.src.graph.state import VideoAuditState
from backend.src.graph.nodes import index_video_node,audit_content_node

#Initialize state graph

def create_graph():
    '''
    constructs and compiles langgrah workflow
    Return:
    Compiled graph
    '''

    workflow = StateGraph(VideoAuditState)

    # add nodes
    workflow.add_node("indexer",index_video_node)
    workflow.add_node("auditor",audit_content_node)

    #edge defenition
    workflow.set_entry_point("indexer")
    workflow.add_edge("indexer","auditor")
    workflow.add_edge("auditor",END)

    #build graph
    app = workflow.compile()
    return app

app = create_graph()