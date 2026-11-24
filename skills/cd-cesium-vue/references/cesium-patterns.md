# Vue-Cesium & CesiumJS patterns and audit checklist

Reference for `cd-cesium-vue`. Applies to both raw `cesium` inside Vue 3 and `vue-cesium`.

## 1. Reactivity & State

| Pattern | Why it matters | Typical severity |
| --- | --- | --- |
| `ref(new Viewer(...))` or storing `Viewer`, `Entity`, `Cesium3DTileset`, `DataSource` inside `reactive()` / Pinia state without `markRaw` / `shallowRef` | Vue's deep `Proxy` wraps Cesium's internal matrices, typed arrays, and WebGL handles, causing severe frame-rate drops and subtle runtime errors. | **High** |
| Mutating hundreds of `Entity` properties inside reactive `watch`ers on every frame | Triggers Vue dependency tracking and Cesium geometry rebuilds synchronously. Batch updates or use `CallbackProperty` / `PrimitiveCollection` / `PointPrimitiveCollection`. | **Medium** |

**Recommended composable pattern (raw `cesium`):**
```ts
import { onUnmounted, shallowRef, markRaw } from 'vue'
import { Viewer } from 'cesium'

export function useCesiumViewer(container: Readonly<Ref<HTMLElement | null>>) {
  const viewer = shallowRef<Viewer | null>(null)

  function init() {
    if (!container.value || viewer.value) return
    viewer.value = markRaw(new Viewer(container.value, {
      requestRenderMode: true,
      maximumRenderTimeChange: Infinity,
    }))
  }

  onUnmounted(() => {
    viewer.value?.destroy()
    viewer.value = null
  })

  return { viewer, init }
}
```

## 2. WebGL & Listener Lifecycle

| Check | Why it matters | Typical severity |
| --- | --- | --- |
| `viewer.destroy()` called in `onUnmounted` (for raw `cesium`) | Browsers limit active WebGL contexts (often 8–16); navigating between routes without destroying `Viewer` leaks GPU memory and eventually blanks the canvas. | **High** |
| `ScreenSpaceEventHandler.destroy()` called in `onUnmounted` | Mouse/pointer handlers outlive the component and retain closures over stale state. | **High** |
| `scene.postRender.addEventListener(...)` / `preRender` / `clock.onTick` / `camera.changed` deregistered on unmount | Duplicate listeners fire after route changes and leak memory. Store the returned remover function and call it in `onUnmounted`. | **High** |
| `isDestroyed()` guarded in async callbacks (e.g. `await Cesium3DTileset.fromUrl(...)` or `GeoJsonDataSource.load(...)`) | If the user navigates away while a tileset or GeoJSON is loading, adding it to a destroyed `viewer` throws a runtime error. | **Medium** |

## 3. Vite Build & Static Assets

| Check | Why it matters | Typical severity |
| --- | --- | --- |
| `CESIUM_BASE_URL` defined and Cesium static folders (`Workers`, `Assets`, `Widgets`, `ThirdParty`) copied in `vite.config.*` (or `vite-plugin-cesium-build` / `vue-cesium` CDN/local config) | Dev mode may appear to work via `node_modules` while `vite build` fails at runtime with 404s for Web Workers and imagery/widget assets. | **High** |
| `cesium/Build/Cesium/Widgets/widgets.css` (or `vue-cesium/dist/index.css`) imported once | Missing CSS breaks the canvas sizing, timeline, and info box layout. | **Medium** |

## 4. Tokens & Security

| Check | Why it matters | Typical severity |
| --- | --- | --- |
| Hardcoded `Ion.defaultAccessToken = "eyJ..."` or tile-provider API keys in `.ts`/`.vue` files | Exposes paid Ion/map quotas in source control and build history. Read from `import.meta.env.VITE_CESIUM_ION_TOKEN`. | **Critical** (real token) / **High** |
| `.env` committed to git | Leaks environment secrets; commit `.env.example` with placeholders only. | **Critical** |

## 5. Performance & Rendering

| Check | Why it matters | Typical severity |
| --- | --- | --- |
| `requestRenderMode: true` considered for mostly static GIS/BIM scenes | Without it, Cesium renders at 60 FPS continuously, draining laptop batteries and heating GPUs even when the camera is idle. (Call `viewer.scene.requestRender()` after programmatic updates.) | **Low** / **Medium** |
| Heavy `postRender` / `preRender` / `onTick` allocations (`new Cartesian3()`, `new Matrix4()`) | Per-frame GC churn causes frame-time spikes; pre-allocate scratch objects outside the callback. | **Medium** |
| 3D Tilesets (`Cesium3DTileset`) tuned (`maximumScreenSpaceError`, `cacheBytes` / `maximumCacheOverflowBytes`) for large models | Unbounded 3D Tiles memory usage can crash mobile or low-VRAM browsers. | **Low** |
| `terrainProvider` / `createWorldTerrainAsync` error handling and fallbacks | Network failures or Ion quota limits should surface a clear UI state rather than an unhandled promise rejection. | **Medium** |
