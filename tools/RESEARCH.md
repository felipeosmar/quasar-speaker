# EasyEDA Pro API Research

**Date:** 2026-02-17
**Goal:** Automate schematic creation for QuasarBox in EasyEDA Pro

## Key Finding: EasyEDA Pro Has a Full Extension API

EasyEDA Pro (v2.2+) has a **completely different API** from EasyEDA Standard. It's NOT the old `easyeda.extension.exec()` / `api('createShape')` approach.

### Pro Extension System Overview

- **Global object:** `eda` (typed as `EDA` class with ~70+ subsystems)
- **Extensions** are JS bundles built with TypeScript + esbuild, packaged as `.zip`
- **SDK:** https://github.com/easyeda/pro-api-sdk
- **Types:** `@jlceda/pro-api-types` (npm, v0.1.175, 16K+ lines of type defs)
- **Docs:** https://prodocs.easyeda.com/en/api/guide/ (partial, many pages 404)
- **Examples:** https://github.com/easyeda (org with `eext-*` repos)
- **Engine requirement:** `"eda": "^3.0.0"` in latest SDK (our v2.2.45 may need older)

### Key APIs for Schematic Automation

#### 1. Search/Find Components by LCSC Part Number
```typescript
// Search by LCSC C-number (e.g., "C2913319" for ESP32-S3-WROOM-1)
const device = await eda.lib_Device.getByLcscIds("C2913319");
// Or search by keyword
const results = await eda.lib_Device.search("ESP32-S3");
```

#### 2. Place Components
```typescript
// Create component at position (x, y) — coordinates in 0.01inch units
const comp = await eda.sch_PrimitiveComponent.create(
    device,     // {libraryUuid, uuid} from search
    100, 200,   // x, y position
    undefined,  // subPartName
    0,          // rotation (degrees)
    false,      // mirror
    true,       // addIntoBom
    true        // addIntoPcb
);
```

#### 3. Create Wires
```typescript
// Wire as array of coordinates [x1,y1, x2,y2, x3,y3, ...]
const wire = await eda.sch_PrimitiveWire.create(
    [100, 200, 200, 200, 200, 300],  // L-shaped wire
    "VCC",      // net name (optional, auto-detected from endpoints)
    null,       // color (default)
    null,       // lineWidth (default)
    null        // lineType (default)
);
```

#### 4. Create Net Flags (Power/GND symbols)
```typescript
// Power flag
const vcc = await eda.sch_PrimitiveComponent.createNetFlag(
    'Power', 'VCC', 100, 150, 0, false
);
// Ground flag
const gnd = await eda.sch_PrimitiveComponent.createNetFlag(
    'Ground', 'GND', 100, 350, 0, false
);
```

#### 5. Create Net Ports (Labels)
```typescript
const port = await eda.sch_PrimitiveComponent.createNetPort(
    'BI', 'SDA', 300, 200, 0, false
);
```

#### 6. Project/Schematic Management
```typescript
// Create project
const projectUuid = await eda.dmt_Project.createProject("QuasarBox");
// Open project
await eda.dmt_Project.openProject(projectUuid);
// Create schematic
const schUuid = await eda.dmt_Schematic.createSchematic();
// Create schematic page
const pageUuid = await eda.dmt_Schematic.createSchematicPage(schUuid);
// Open the page in editor
await eda.dmt_EditorControl.openDocument(pageUuid);
// Save
await eda.sch_Document.save();
```

#### 7. Modify Components
```typescript
await eda.sch_PrimitiveComponent.modify(primitiveId, {
    x: 200, y: 300,
    designator: "U1",
    manufacturer: "Espressif",
    manufacturerId: "ESP32-S3-WROOM-1-N16R8"
});
```

#### 8. Get Component Pins
```typescript
const pins = await eda.sch_PrimitiveComponent.getAllPinsByPrimitiveId(primitiveId);
// Each pin has position, number, name, net info
```

### Coordinate System
- SCH coordinates: units of **0.01 inch** (same as 10 mil)
- Positive X = right, Positive Y = down
- Origin can be set but defaults to canvas (0,0)

## Automation Strategy: CDP + JS Injection

Since building a full extension requires npm/esbuild/packaging, the **fastest approach** is:

1. **Use CDP** to connect to EasyEDA Pro (already working)
2. **Inject JavaScript** via `Runtime.evaluate` that calls the `eda.*` APIs
3. The `eda` global is available in the **main frame** context (not iframes)

### Critical: Frame Targeting

EasyEDA Pro uses iframes. The `eda` object lives in the **schematic editor iframe** (entry=sch), NOT the main page. We need to:

1. Use `Page.getFrameTree()` to find the sch iframe
2. Use `Runtime.evaluate` with the correct `contextId` for that frame
3. Or use `Target.attachToTarget` for the iframe target

### Python CDP Automation Flow

```python
# 1. Connect to CDP
# 2. Find the correct execution context (schematic iframe)
# 3. Inject async JS that calls eda.* APIs
# 4. Return results as JSON
```

## Alternative Approaches

### A. Build a Proper Extension (Best long-term)
- Clone pro-api-sdk, write TypeScript extension
- Build with `npm run build`
- Install in EasyEDA Pro via Extension Manager
- Extension exposes HTTP server or MessageBus for external control
- **Pros:** Full API access, proper types, stable
- **Cons:** Requires Node.js toolchain, extension packaging

### B. CDP + Runtime.evaluate (Current approach, improved)
- Inject JS directly via CDP
- Call `eda.*` APIs through evaluate
- **Pros:** No extension packaging needed, quick iteration
- **Cons:** Frame context issues, async handling, no TypeScript types

### C. Direct File Manipulation
- EasyEDA Pro uses cloud sync, files stored on server
- No local file format to manipulate
- **Not viable** for programmatic creation

## Reference Links

- Extension API guide: https://prodocs.easyeda.com/en/api/guide/
- SDK: https://github.com/easyeda/pro-api-sdk
- Types: `npm pack @jlceda/pro-api-types`
- Example extensions:
  - https://github.com/easyeda/eext-freerouting-intergration
  - https://github.com/easyeda/eext-update-components-attributes
  - https://github.com/easyeda/eext-api-debug-tool
  - https://github.com/easyeda/eext-qrcode-generator
- Extension Store (China): https://ext.lceda.cn/
- Old Standard API (different!): https://docs.easyeda.com/en/API/EasyEDA-API/

## Important Notes

1. **Pro ≠ Standard**: The `api('createShape')` style from Standard does NOT exist in Pro
2. **`eda` global**: All Pro APIs go through the `eda` object
3. **Async**: All Pro APIs are async (return Promises)
4. **Engine version**: SDK requires `eda >= ^3.0.0`, our v2.2.45 may have older API
5. **IFrame architecture**: Extensions can open iframes with `eda.sys_IFrame.openIFrame()`
6. **MessageBus**: Extensions communicate via `eda.sys_MessageBus.publish/subscribe`
