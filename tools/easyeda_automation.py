#!/usr/bin/env python3
"""
EasyEDA Pro Automation via CDP + Extension API

Uses Chrome DevTools Protocol to inject JavaScript that calls the
EasyEDA Pro Extension API (eda.* global object).

Requirements:
  pip install websocket-client

Usage:
  from easyeda_automation import EasyEDAPro
  
  eda = EasyEDAPro("192.168.15.13", 9222)
  eda.connect()
  
  # Search component by LCSC number
  device = eda.find_component_by_lcsc("C2913319")
  
  # Place component
  comp = eda.place_component(device, x=200, y=200)
  
  # Create wire
  eda.create_wire([200, 250, 300, 250])
  
  # Add power/ground flags
  eda.create_net_flag("Power", "3V3", 200, 150)
  eda.create_net_flag("Ground", "GND", 200, 350)
  
  # Save
  eda.save()
"""

import json
import time
import urllib.request
from typing import Any, Optional

import websocket


class EasyEDAPro:
    """Automate EasyEDA Pro via CDP WebSocket + eda.* Extension API."""

    def __init__(self, host: str = "192.168.15.13", port: int = 9222):
        self.host = host
        self.port = port
        self.ws: Optional[websocket.WebSocket] = None
        self._msg_id = 0
        self._execution_context_id: Optional[int] = None

    # ── Connection ──────────────────────────────────────────────

    def connect(self):
        """Connect to EasyEDA Pro via CDP and find the correct execution context."""
        # Find the main page
        pages = self._get_pages()
        main_page = None
        for p in pages:
            if p.get("type") == "page" and "easyeda" in p.get("url", "").lower():
                main_page = p
                break
        if not main_page:
            # Fall back to first page
            main_page = pages[0] if pages else None
        if not main_page:
            raise ConnectionError("No EasyEDA Pro page found on CDP")

        ws_url = main_page["webSocketDebuggerUrl"]
        print(f"[CDP] Connecting to {main_page.get('title', 'unknown')}...")
        self.ws = websocket.create_connection(ws_url, timeout=30)

        # Find the correct execution context for eda global
        self._find_eda_context()
        print(f"[CDP] Connected! Context ID: {self._execution_context_id}")

    def disconnect(self):
        if self.ws:
            self.ws.close()
            self.ws = None

    def _get_pages(self) -> list:
        url = f"http://{self.host}:{self.port}/json"
        with urllib.request.urlopen(url, timeout=5) as resp:
            return json.loads(resp.read())

    def _find_eda_context(self):
        """Find the execution context where `eda` global is available."""
        # Enable Runtime to get context notifications
        self._send("Runtime.enable")
        time.sleep(0.5)

        # Try to find eda in the main context first
        for ctx_id in range(1, 20):
            try:
                result = self._evaluate("typeof eda !== 'undefined' ? 'found' : 'not_found'", context_id=ctx_id)
                if result == "found":
                    self._execution_context_id = ctx_id
                    return
            except Exception:
                continue

        # If not found, try enabling frame targets
        self._send("Target.setAutoAttach", {
            "autoAttach": True,
            "waitForDebuggerOnStart": False,
            "flatten": True
        })
        time.sleep(1)

        # Try again with higher context IDs
        for ctx_id in range(1, 50):
            try:
                result = self._evaluate("typeof eda !== 'undefined' ? 'found' : 'not_found'", context_id=ctx_id)
                if result == "found":
                    self._execution_context_id = ctx_id
                    return
            except Exception:
                continue

        raise RuntimeError(
            "Could not find execution context with `eda` global. "
            "Make sure EasyEDA Pro has a project open with a schematic tab active."
        )

    # ── CDP Communication ───────────────────────────────────────

    def _send(self, method: str, params: dict = None) -> dict:
        self._msg_id += 1
        msg = {"id": self._msg_id, "method": method}
        if params:
            msg["params"] = params
        self.ws.send(json.dumps(msg))

        # Read responses until we get our reply
        deadline = time.time() + 30
        while time.time() < deadline:
            raw = self.ws.recv()
            resp = json.loads(raw)
            if resp.get("id") == self._msg_id:
                if "error" in resp:
                    raise RuntimeError(f"CDP error: {resp['error']}")
                return resp.get("result", {})
        raise TimeoutError(f"Timeout waiting for CDP response to {method}")

    def _evaluate(self, expression: str, context_id: int = None, await_promise: bool = False) -> Any:
        """Evaluate JS expression in the eda context."""
        ctx = context_id or self._execution_context_id
        params = {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": await_promise,
        }
        if ctx:
            params["contextId"] = ctx

        result = self._send("Runtime.evaluate", params)
        
        if "exceptionDetails" in result:
            exc = result["exceptionDetails"]
            text = exc.get("text", "")
            desc = exc.get("exception", {}).get("description", "")
            raise RuntimeError(f"JS Error: {text} {desc}")

        r = result.get("result", {})
        if r.get("type") == "undefined":
            return None
        return r.get("value", r.get("description"))

    def _eval_async(self, expression: str) -> Any:
        """Evaluate an async JS expression (wraps in async IIFE, awaits promise)."""
        wrapped = f"(async () => {{ {expression} }})()"
        return self._evaluate(wrapped, await_promise=True)

    def _eval_async_json(self, expression: str) -> Any:
        """Evaluate async JS, return result as JSON-parsed Python object."""
        wrapped = f"(async () => {{ const __r = await (async () => {{ {expression} }})(); return JSON.stringify(__r); }})()"
        raw = self._evaluate(wrapped, await_promise=True)
        if raw is None:
            return None
        return json.loads(raw)

    # ── High-Level API ──────────────────────────────────────────

    # -- Component Search --

    def find_component_by_lcsc(self, lcsc_id: str) -> Optional[dict]:
        """Find a component by LCSC C-number (e.g., 'C2913319').
        
        Returns dict with {libraryUuid, uuid, name, ...} or None.
        """
        result = self._eval_async_json(f"""
            const items = await eda.lib_Device.getByLcscIds('{lcsc_id}');
            if (Array.isArray(items) && items.length > 0) {{
                const d = items[0];
                return {{
                    libraryUuid: d.libraryUuid || d.library_uuid,
                    uuid: d.uuid,
                    name: d.name || d.display_title || '{lcsc_id}',
                    lcsc: '{lcsc_id}'
                }};
            }}
            return null;
        """)
        return result

    def search_component(self, keyword: str, limit: int = 5) -> list:
        """Search components by keyword. Returns list of device info dicts."""
        return self._eval_async_json(f"""
            const items = await eda.lib_Device.search('{keyword}', undefined, undefined, undefined, {limit});
            return items.map(d => ({{
                libraryUuid: d.libraryUuid || d.library_uuid,
                uuid: d.uuid,
                name: d.name || d.display_title || '',
                description: d.description || ''
            }}));
        """) or []

    # -- Component Placement --

    def place_component(self, device: dict, x: float, y: float,
                        rotation: float = 0, mirror: bool = False,
                        designator: str = None) -> Optional[dict]:
        """Place a component on the schematic.
        
        Args:
            device: dict with {libraryUuid, uuid} from find/search
            x, y: position in schematic coordinates (0.01 inch units)
            rotation: degrees (0, 90, 180, 270)
            mirror: horizontal mirror
            designator: e.g., "U1", "R1" (optional, auto-assigned if None)
        
        Returns: primitive info dict or None
        """
        lib_uuid = device["libraryUuid"]
        dev_uuid = device["uuid"]
        mirror_js = "true" if mirror else "false"
        
        result = self._eval_async_json(f"""
            const comp = await eda.sch_PrimitiveComponent.create(
                {{libraryUuid: '{lib_uuid}', uuid: '{dev_uuid}'}},
                {x}, {y},
                undefined,  // subPartName
                {rotation},
                {mirror_js},
                true,   // addIntoBom
                true    // addIntoPcb
            );
            if (!comp) return null;
            const pid = comp.getState_PrimitiveId ? comp.getState_PrimitiveId() : comp.primitiveId;
            const des = comp.getState_Designator ? comp.getState_Designator() : '';
            return {{primitiveId: pid, designator: des}};
        """)

        if result and designator:
            self.modify_component(result["primitiveId"], designator=designator)

        return result

    def modify_component(self, primitive_id: str, **kwargs) -> bool:
        """Modify a placed component's properties.
        
        Supported kwargs: x, y, rotation, mirror, designator, 
            manufacturer, manufacturerId, supplier, supplierId
        """
        props = {}
        for k in ["x", "y", "rotation", "designator", "manufacturer",
                   "manufacturerId", "supplier", "supplierId"]:
            if k in kwargs:
                v = kwargs[k]
                props[k] = v

        if "mirror" in kwargs:
            props["mirror"] = kwargs["mirror"]

        props_json = json.dumps(props)
        return self._eval_async_json(f"""
            const r = await eda.sch_PrimitiveComponent.modify('{primitive_id}', {props_json});
            return r ? true : false;
        """) or False

    # -- Wires --

    def create_wire(self, points: list, net: str = None) -> Optional[dict]:
        """Create a wire on the schematic.
        
        Args:
            points: flat array [x1,y1, x2,y2, ...] or nested [[x1,y1,x2,y2,...], ...]
            net: optional net name
        
        Returns: wire primitive info or None
        """
        points_json = json.dumps(points)
        net_arg = f"'{net}'" if net else "undefined"
        
        return self._eval_async_json(f"""
            const wire = await eda.sch_PrimitiveWire.create(
                {points_json}, {net_arg}
            );
            if (!wire) return null;
            const pid = wire.getState_PrimitiveId ? wire.getState_PrimitiveId() : wire.primitiveId;
            return {{primitiveId: pid}};
        """)

    # -- Net Flags (Power/GND) --

    def create_net_flag(self, flag_type: str, net: str, x: float, y: float,
                        rotation: float = 0) -> Optional[dict]:
        """Create a power/ground net flag.
        
        Args:
            flag_type: 'Power', 'Ground', 'AnalogGround', 'ProtectGround'
            net: net name (e.g., 'VCC', '3V3', 'GND')
            x, y: position
            rotation: degrees
        """
        return self._eval_async_json(f"""
            const flag = await eda.sch_PrimitiveComponent.createNetFlag(
                '{flag_type}', '{net}', {x}, {y}, {rotation}, false
            );
            if (!flag) return null;
            const pid = flag.getState_PrimitiveId ? flag.getState_PrimitiveId() : flag.primitiveId;
            return {{primitiveId: pid, net: '{net}'}};
        """)

    # -- Net Ports (Labels) --

    def create_net_port(self, direction: str, net: str, x: float, y: float,
                        rotation: float = 0) -> Optional[dict]:
        """Create a net port (label).
        
        Args:
            direction: 'IN', 'OUT', 'BI'
            net: net name
            x, y: position
            rotation: degrees
        """
        return self._eval_async_json(f"""
            const port = await eda.sch_PrimitiveComponent.createNetPort(
                '{direction}', '{net}', {x}, {y}, {rotation}, false
            );
            if (!port) return null;
            const pid = port.getState_PrimitiveId ? port.getState_PrimitiveId() : port.primitiveId;
            return {{primitiveId: pid, net: '{net}'}};
        """)

    # -- Text --

    def create_text(self, text: str, x: float, y: float,
                    font_size: float = 8, rotation: float = 0) -> Optional[dict]:
        """Create a text annotation."""
        text_escaped = text.replace("'", "\\'").replace("\n", "\\n")
        return self._eval_async_json(f"""
            const t = await eda.sch_PrimitiveText.create(
                '{text_escaped}', {x}, {y}, {font_size}, {rotation}
            );
            if (!t) return null;
            const pid = t.getState_PrimitiveId ? t.getState_PrimitiveId() : t.primitiveId;
            return {{primitiveId: pid}};
        """)

    # -- Project/Schematic Management --

    def get_current_project(self) -> Optional[dict]:
        """Get info about the currently open project."""
        return self._eval_async_json("""
            const info = await eda.dmt_Project.getCurrentProjectInfo();
            if (!info) return null;
            return {
                uuid: info.uuid,
                name: info.name || info.friendlyName,
                schematics: (info.schematics || []).map(s => ({
                    uuid: s.uuid, name: s.name,
                    pages: (s.pages || []).map(p => ({uuid: p.uuid, name: p.name}))
                }))
            };
        """)

    def create_project(self, name: str) -> Optional[str]:
        """Create a new project. Returns project UUID."""
        return self._eval_async_json(f"""
            const uuid = await eda.dmt_Project.createProject('{name}');
            return uuid;
        """)

    def create_schematic(self, board_name: str = None) -> Optional[str]:
        """Create a new schematic. Returns schematic UUID."""
        board_arg = f"'{board_name}'" if board_name else "undefined"
        return self._eval_async_json(f"""
            const uuid = await eda.dmt_Schematic.createSchematic({board_arg});
            return uuid;
        """)

    def create_schematic_page(self, schematic_uuid: str) -> Optional[str]:
        """Create a new schematic page. Returns page UUID."""
        return self._eval_async_json(f"""
            const uuid = await eda.dmt_Schematic.createSchematicPage('{schematic_uuid}');
            return uuid;
        """)

    def open_document(self, uuid: str) -> Optional[str]:
        """Open a document (schematic page, PCB, etc.) in the editor."""
        return self._eval_async_json(f"""
            const tabId = await eda.dmt_EditorControl.openDocument('{uuid}');
            return tabId;
        """)

    def save(self) -> bool:
        """Save the current schematic document."""
        return self._eval_async_json("""
            const r = await eda.sch_Document.save();
            return r;
        """) or False

    # -- Component Info --

    def get_all_components(self) -> list:
        """Get all components on the current schematic page."""
        return self._eval_async_json("""
            const comps = await eda.sch_PrimitiveComponent.getAll();
            return comps.map(c => ({
                primitiveId: c.getState_PrimitiveId ? c.getState_PrimitiveId() : c.primitiveId,
                designator: c.getState_Designator ? c.getState_Designator() : '',
                name: c.getState_SubPartName ? c.getState_SubPartName() : '',
                x: c.getState_X ? c.getState_X() : 0,
                y: c.getState_Y ? c.getState_Y() : 0
            }));
        """) or []

    def get_component_pins(self, primitive_id: str) -> list:
        """Get all pins of a component."""
        return self._eval_async_json(f"""
            const pins = await eda.sch_PrimitiveComponent.getAllPinsByPrimitiveId('{primitive_id}');
            if (!pins) return [];
            return pins.map(p => ({{
                number: p.getState_Number ? p.getState_Number() : p.number || '',
                name: p.getState_Name ? p.getState_Name() : p.name || '',
                x: p.getState_X ? p.getState_X() : p.x || 0,
                y: p.getState_Y ? p.getState_Y() : p.y || 0,
                net: p.getState_Net ? p.getState_Net() : p.net || ''
            }}));
        """) or []

    # -- Utilities --

    def check_eda_available(self) -> bool:
        """Check if the eda global is accessible."""
        try:
            result = self._evaluate("typeof eda !== 'undefined' ? 'yes' : 'no'")
            return result == "yes"
        except Exception:
            return False

    def get_eda_version(self) -> Optional[str]:
        """Get EasyEDA Pro version info."""
        try:
            return self._eval_async_json("""
                const env = await eda.sys_Environment.getAppVersion();
                return env;
            """)
        except Exception:
            return None

    def eval_js(self, code: str) -> Any:
        """Execute arbitrary async JS code in the eda context. For debugging."""
        return self._eval_async_json(code)


# ── CLI Demo ────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    host = sys.argv[1] if len(sys.argv) > 1 else "192.168.15.13"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 9222

    print(f"Connecting to EasyEDA Pro at {host}:{port}...")
    eda = EasyEDAPro(host, port)

    try:
        eda.connect()
    except Exception as e:
        print(f"Connection failed: {e}")
        print("\nMake sure EasyEDA Pro is running with:")
        print(f"  easyeda-pro --remote-debugging-port={port} --remote-allow-origins=*")
        print("And that a project with a schematic is open.")
        sys.exit(1)

    print("\n✅ Connected to EasyEDA Pro!")
    print(f"   eda available: {eda.check_eda_available()}")

    # Show current project info
    project = eda.get_current_project()
    if project:
        print(f"   Project: {project.get('name', 'unknown')}")
        for sch in project.get("schematics", []):
            print(f"   Schematic: {sch['name']}")
            for page in sch.get("pages", []):
                print(f"     Page: {page['name']}")

    # Show existing components
    comps = eda.get_all_components()
    if comps:
        print(f"\n   Components on page ({len(comps)}):")
        for c in comps[:10]:
            print(f"     {c.get('designator', '?')} - {c.get('name', '')} @ ({c.get('x')}, {c.get('y')})")

    # Demo: search for a component
    print("\n   Searching for ESP32-S3...")
    results = eda.search_component("ESP32-S3-WROOM", limit=3)
    for r in results:
        print(f"     Found: {r.get('name', '')} ({r.get('uuid', '')[:8]}...)")

    eda.disconnect()
    print("\n✅ Done!")
