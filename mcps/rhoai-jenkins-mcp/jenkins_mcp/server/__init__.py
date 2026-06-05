from mcp.server.fastmcp import FastMCP
import importlib
import pkgutil
import sys

mcp = FastMCP('rhoai-jenkins')

print(f"Importing tools from {__name__}")
package = __name__
for _, module_name, ispkg in pkgutil.iter_modules(__path__):
    print(f"Importing {module_name}")
    importlib.import_module(f"{package}.{module_name}")
