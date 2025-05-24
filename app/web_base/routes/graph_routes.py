from fastapi import APIRouter, Response
from fastapi.responses import FileResponse
import os
from pathlib import Path

from app.AI.workflows.graph.main_graph import graph

router = APIRouter(prefix="/graph", tags=["graph"])

@router.get("/chatbot/graph/image")
async def get_graph_image():
    """
    Get the current workflow graph visualization as a PNG image.
    """
    # Generate the graph image
    graph.get_graph(xray=True).draw_mermaid_png(output_file_path="graph.png")

    # Get the absolute path to the generated image
    current_dir = Path(__file__).parent.parent.parent
    image_path = current_dir / "graph.png"

    # Check if the image exists
    if not image_path.exists():
        return Response(status_code=404, content="Graph image not found")

    # Return the image file
    return FileResponse(
        path=image_path,
        media_type="image/png",
        filename="workflow_graph.png"
    )