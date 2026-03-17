# A9_Briefing_Agent Concept

## Purpose
To synthesize complex information from multiple Agent9 sources (agent reports, meeting minutes, PRDs) into high-level, easily digestible formats like mindmaps and audio summaries. This agent serves key stakeholders by providing tailored briefings that accelerate comprehension and decision-making.

---

## Personas Served
- **Investor:** Receives concise, audio-based executive summaries on project progress, risk, and market value.
- **Product Owner / Business Owner:** Uses mindmaps and audio reports to maintain a high-level view and communicate project status.
- **Lead Engineer / Technical Architect:** Uses mindmaps to visualize system architecture, agent dependencies, and data flow.
- **Analyst / End User:** Consumes simplified summaries to understand the impact of ongoing implementations.

---

## Capabilities

### 1. Mindmap Generation
- **Input:** A list of source URIs (documents, agent report IDs).
- **Process:**
    1. Fetches and aggregates text from sources.
    2. Uses an LLM to perform entity and relationship extraction (e.g., identifies agents, action items, risks, dependencies, and stakeholders).
    3. Structures the output as a graph (nodes and edges) with labels and details.
- **Output:** A JSON object representing the mindmap, ready for front-end rendering.

### 2. Audio Overview Generation
- **Input:** A list of source URIs and a target persona.
- **Process:**
    1. Fetches and aggregates text from sources.
    2. Generates a tailored summary script based on the target persona's interests (e.g., financial metrics for CFO, operational risks for COO).
    3. Uses a Text-to-Speech (TTS) API to convert the script into an audio file.
- **Output:** A URL to the generated audio file, along with a transcript and key bullet points.

---

## Workflow Stage Integrations
The agent can tailor audio overviews based on the specific Agent9 workflow phase:
- **Situation Awareness (SA):** "Flash Briefings" summarizing KPI breaches and anomalies.
- **Deep Analysis (DA):** Narrative summaries of Kepner-Tregoe (Is/Is Not) root cause findings.
- **Market Analysis (MA):** "Intel Briefs" highlighting competitor moves and industry headwinds/tailwinds.
- **Solution Finding (SF):** "Council Debates" detailing the trade-offs of proposed options (can utilize conversational/podcast styles).
- **Value Assurance (VA):** "ROI Post-Mortems" reporting on the success of implemented changes vs. market baselines.

---

## Evolution of the Executive Briefing
The `A9_Briefing_Agent` fundamentally evolves the concept of an "Executive Briefing" within the Agent9 Decision Studio. It transforms the briefing from a static, periodic report into a dynamic, multi-format, and personalized intelligence service:

- **From Static Report to On-Demand Audio Intelligence:** Executives can consume updates passively (e.g., during commutes). This includes 60-second "Flash Briefings" for Situation Awareness, narrative "Detective's Summaries" for Deep Analysis, and multi-speaker "Council Debates" simulating the Solution Finder's output.
- **From Flat Data to Visualized Interconnections:** Mindmaps provide a crucial visual dimension, clarifying complex technical dependencies for engineers while connecting specific risks directly to business objectives for investors and product owners.
- **From Manual Compilation to Automated, Persona-Tailored Synthesis:** Briefings are generated on-demand, pulling the absolute latest information from across the Agent9 ecosystem. The same underlying data is automatically tailored to highlight ROI and risk for an Investor, or architecture and data flow for a Technical Architect.

---

## A2A Protocol Enforcement (Pydantic Models)

The `A9_Briefing_Agent` will strictly adhere to the A2A protocol, using Pydantic models for all entrypoints.

```python
from pydantic import BaseModel, Field
from typing import List, Literal, Dict

# --- Input Model ---

class BriefingRequest(BaseModel):
    """
    Request to the BriefingAgent to generate a summary from source materials.
    """
    source_uris: List[str] = Field(
        ...,
        description="A list of URIs for source documents, agent reports, or meeting notes."
    )
    output_format: Literal["mindmap", "audio_overview"] = Field(
        ...,
        description="The desired output format."
    )
    target_persona: Literal["investor", "product_owner", "lead_engineer", "end_user"] = Field(
        default="product_owner",
        description="The target audience for the briefing, used to tailor the content."
    )
    workflow_stage: Literal["SA", "DA", "MA", "SF", "VA", "general"] = Field(
        default="general",
        description="The stage of the Agent9 workflow this briefing covers, used to frame the narrative style."
    )

# --- Output Models ---

class MindmapNode(BaseModel):
    id: str
    label: str
    group: str # e.g., 'Risk', 'Persona', 'Action Item'
    details: Dict

class MindmapEdge(BaseModel):
    from_node: str
    to_node: str
    label: str

class MindmapOutput(BaseModel):
    """
    The structured output for a mind map visualization.
    """
    nodes: List[MindmapNode]
    edges: List[MindmapEdge]
    summary: str = Field(description="A high-level text summary of the mind map's content.")

class AudioOverviewOutput(BaseModel):
    """
    The output containing the audio summary.
    """
    audio_file_url: str = Field(description="A URL to the generated MP3 audio file.")
    transcript: str = Field(description="The full text transcript of the audio overview.")
    summary_points: List[str] = Field(description="Key bullet points covered in the audio.")
```

---

## Integration
- The `A9_Orchestrator_Agent` will be responsible for routing requests to the `A9_Briefing_Agent`.
- It can be triggered on-demand by a user or automatically after significant events (e.g., completion of a major implementation phase).
- The agent will pull data from other agents like `A9_Implementation_Tracker_Agent` and `A9_Risk_Management_Agent`.
