"""
Agent Orchestrator — MCP-style ask-clarify-decide loop.
Owner: Agoro Oluwatimilehin

Pipeline:
voice intake -> intent/entity extraction -> trust score -> 
  low risk: release
  medium/high risk: soft hold -> TTS question + visual confirmation card -> decision agent
"""
