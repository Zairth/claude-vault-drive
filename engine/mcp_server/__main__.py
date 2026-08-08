# mcp_server/__main__.py
"""Point d'entrée stdio : `python -m mcp_server` (lancé par le plugin via uv).

stdout est réservé au JSON-RPC du protocole MCP.
"""

from mcp_server.server import server

server.run()
