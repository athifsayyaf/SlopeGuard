const modules = [
  { id: "project", icon: "project", title: "Project", tabs: ["Setup", "Study Area"] },
  { id: "dem", icon: "terrain-icon", title: "DEM", tabs: ["Slope", "Aspect", "TWI", "Hillshade"] },
  { id: "sentinel2", icon: "raster", title: "Sentinel-2", tabs: ["NDVI", "EVI", "Bare Soil Index", "NDWI", "LULC Classification"] },
  { id: "insar", icon: "orbit", title: "Sentinel-1/InSAR", tabs: ["Data Source", "Sentinel-1", "NISAR", "Preprocessed InSAR Upload", "Velocity Map", "Coherence Mask"] },
  { id: "inventory", icon: "polygon", title: "Landslide Inventory", tabs: ["Upload", "Rasterize", "Align"] },
  { id: "stack", icon: "layers", title: "Stack Builder", tabs: ["Inputs", "Alignment", "Export"] },
  { id: "ml", icon: "model", title: "ML Model", tabs: ["Feature Selection", "Train Model", "Spatial Cross Validation", "Compare Models", "Susceptibility Map"] },
  { id: "interpretation", icon: "inspect", title: "Interpretation", tabs: ["AI Assistant", "Uncertainty", "Next Steps"] },
  { id: "report", icon: "layout", title: "Report", tabs: ["Report Generator", "Map Layout", "One Slide"] },
];

const examples = {
  root: "D:\\The_worker\\Non_work\\PhD_related\\sansar_phD\\Assignment\\Work",
  dem: "D:\\The_worker\\Non_work\\PhD_related\\sansar_phD\\Assignment\\Work\\Download_DEM\\rasters_COP30\\output_hh.tif",
  ndvi: "D:\\The_worker\\Non_work\\PhD_related\\sansar_phD\\Assignment\\Work\\Results\\FROM_s2\\joshimath_ndvi.tif",
  insar: "D:\\The_worker\\Non_work\\PhD_related\\sansar_phD\\Assignment\\Work\\InSAR\\Joshimath\\jOSHIMATH_velocity_ps.tif",
  inventory: "D:\\The_worker\\Non_work\\PhD_related\\sansar_phD\\Assignment\\Work\\Downloaded_invent\\JOshimath\\1_20260501161152176\\landslide_point_20260501161135235\\landslide_point_20260501161135235.shp",
  output: "E:\\Lenovo_path_moved\\moved_due_to_storageissue\\New project\\slideagent-ai\\outputs",
};

let state = { module: "project", tab: "Setup", activeJob: null, detailsOpen: false, outputsOpen: false };

function el(id) { return document.getElementById(id); }

function renderNav() {
  const nav = el("moduleNav");
  nav.innerHTML = "";
  modules.forEach((m) => {
    const btn = document.createElement("button");
    btn.className = m.id === state.module ? "active" : "";
    btn.innerHTML = `<span class="gis-icon ${m.icon}" aria-hidden="true"></span><span>${m.title}</span>`;
    btn.onclick = () => {
      state.module = m.id;
      state.tab = m.tabs[0];
      render();
    };
    nav.appendChild(btn);
  });
}

function activeModule() {
  return modules.find((m) => m.id === state.module);
}

function field(id, label, value = "", wide = false, type = "text") {
  return `<div class="field ${wide ? "wide" : ""}">
    <label for="${id}">${label}</label>
    <input id="${id}" type="${type}" value="${value}">
  </div>`;
}

function selectField(id, label, options, value = "") {
  return `<div class="field">
    <label for="${id}">${label}</label>
    <select id="${id}">${options.map((o) => `<option ${o === value ? "selected" : ""}>${o}</option>`).join("")}</select>
  </div>`;
}

function tabs(m) {
  return `<div class="tabs">${m.tabs.map((t) => `<button class="${t === state.tab ? "active" : ""}" data-tab="${t}">${t}</button>`).join("")}</div>`;
}

function renderProject() {
  return `${tabs(activeModule())}
    <h3>Project Setup</h3>
    <div class="form-grid">
      ${field("project_name", "Project name", "Kuwari Uttarakhand Monitoring", true)}
      ${field("study_area_name", "Study area", "Kuwari/Joshimath, Uttarakhand", true)}
      ${field("crs", "Analysis CRS", "EPSG:32644")}
      ${field("resolution_m", "Resolution (m)", "30", false, "number")}
      ${field("output_folder", "Output folder", examples.output, true)}
      ${field("aoi_vector", "AOI shapefile or GeoJSON", "", true)}
    </div>
    <button class="primary" onclick="saveProject()">Save project_config.json</button>
    <p class="hint">The project file stores CRS, resolution, output paths, AOI, and default data sources for reproducible runs.</p>`;
}

function renderDEM() {
  const tool = state.tab.toLowerCase();
  return `${tabs(activeModule())}
    <h3>${state.tab}</h3>
    <div class="form-grid">
      ${field("dem_path", "DEM GeoTIFF", examples.dem, true)}
      ${field("dem_crs", "Output CRS", "EPSG:32644")}
      ${field("dem_res", "Output resolution (m)", "30", false, "number")}
      ${selectField("nodata", "Nodata handling", ["mask", "interpolate median", "strict"])}
      ${selectField("smooth", "Smoothing", ["none", "3x3 mean", "gaussian"])}
      ${field("dem_output", "Output folder", `${examples.output}\\dem`, true)}
    </div>
    <button class="primary" onclick="runTool('dem', {tool: '${tool}', dem_path: val('dem_path'), crs: val('dem_crs'), resolution_m: val('dem_res'), output_folder: val('dem_output')})">Run ${state.tab}</button>
    <p class="hint">Expected outputs: slope.tif, aspect.tif, twi.tif, hillshade.tif. CRS, transform, nodata, and metadata are preserved in GeoTIFF outputs.</p>`;
}

function renderSentinel2() {
  const toolMap = { "NDVI": "ndvi", "EVI": "evi", "Bare Soil Index": "bsi", "NDWI": "ndwi", "LULC Classification": "lulc" };
  const tool = toolMap[state.tab];
  return `${tabs(activeModule())}
    <h3>${state.tab}</h3>
    <div class="form-grid">
      ${field("red_band", "Red band", "", true)}
      ${field("nir_band", "NIR band", "", true)}
      ${field("blue_band", "Blue band", "", true)}
      ${field("swir_band", "SWIR band", "", true)}
      ${selectField("cloud_mask", "Cloud mask", ["none", "SCL mask", "QA60 mask"])}
      ${selectField("resampling", "Resampling", ["bilinear", "nearest", "cubic"])}
      ${field("s2_output", "Output folder", `${examples.output}\\sentinel2`, true)}
    </div>
    <button class="primary" onclick="runTool('sentinel2', {tool: '${tool}', red_band: val('red_band'), nir_band: val('nir_band'), blue_band: val('blue_band'), swir_band: val('swir_band'), output_folder: val('s2_output')})">Run ${state.tab}</button>
    <p class="hint">For a precomputed NDVI raster, add it directly in Stack Builder. This panel calculates indices from bands.</p>`;
}

function renderInSAR() {
  return `${tabs(activeModule())}
    <h3>${state.tab}</h3>
    <div class="form-grid">
      ${selectField("insar_source", "Data source", ["Preprocessed InSAR upload", "Sentinel-1 SLC", "NISAR future data", "COMET-LiCS / LiCSBAS"])}
      ${field("min_lat", "Min latitude", "30.40")}
      ${field("max_lat", "Max latitude", "30.68")}
      ${field("min_lon", "Min longitude", "79.47")}
      ${field("max_lon", "Max longitude", "79.82")}
      ${selectField("orbit", "Orbit direction", ["ascending", "descending", "both"])}
      ${field("date_range", "Date range", "2024-10-31 to 2025-04-29", true)}
      ${field("velocity_path", "LOS velocity raster", examples.insar, true)}
      ${field("coherence_path", "Mean coherence raster", "", true)}
      ${field("insar_output", "Output folder", `${examples.output}\\insar`, true)}
    </div>
    <button class="primary" onclick="runTool('insar', {mode: val('insar_source'), velocity_path: val('velocity_path'), coherence_path: val('coherence_path'), output_folder: val('insar_output')})">Register InSAR Layers</button>
    <p class="hint">When coherence is available, SlopeGuard AI exports mean_coherence.tif and coherence_mask.tif. NISAR is modeled as a future data source entry point.</p>`;
}

function renderInventory() {
  return `${tabs(activeModule())}
    <h3>Landslide Inventory</h3>
    <div class="form-grid">
      ${field("inventory_path", "Inventory shapefile, GeoJSON, CSV, or raster", examples.inventory, true)}
      ${field("reference_grid", "Reference grid", `${examples.output}\\dem\\slope.tif`, true)}
      ${selectField("inventory_type", "Inventory type", ["point", "polygon", "raster"])}
      ${field("buffer_m", "Presence buffer (m)", "30", false, "number")}
      ${field("inventory_output", "Output folder", `${examples.output}\\inventory`, true)}
    </div>
    <button class="primary" onclick="runTool('inventory', {inventory_path: val('inventory_path'), reference_grid: val('reference_grid'), inventory_type: val('inventory_type'), buffer_m: val('buffer_m'), output_folder: val('inventory_output')})">Create landslide_mask.tif</button>
    <p class="hint">Output mask convention: 1 = landslide, 0 = non-landslide. Keep the mask aligned to the DEM grid.</p>`;
}

function renderStack() {
  return `${tabs(activeModule())}
    <h3>Analysis Stack</h3>
    <div class="field wide">
      <label>Layer manifest JSON</label>
      <textarea id="layer_manifest">[
  {"name":"slope","path":"outputs/dem/slope.tif"},
  {"name":"aspect","path":"outputs/dem/aspect.tif"},
  {"name":"twi","path":"outputs/dem/twi.tif"},
  {"name":"ndvi","path":"${examples.ndvi}"},
  {"name":"los_velocity","path":"${examples.insar}"},
  {"name":"landslide_mask","path":"outputs/inventory/landslide_mask.tif","role":"target"}
]</textarea>
    </div>
    <div class="form-grid">
      ${field("stack_crs", "Target CRS", "EPSG:32644")}
      ${field("stack_res", "Resolution (m)", "30", false, "number")}
      ${selectField("stack_nodata", "Nodata strategy", ["drop pixels", "median impute", "mask only"])}
      ${field("stack_output", "Output folder", `${examples.output}\\stack`, true)}
    </div>
    <button class="primary" onclick="runStack()">Build Stack</button>
    <p class="hint">Outputs: feature_stack.tif and feature_table.csv, with all layers clipped, resampled, reprojected, and documented.</p>`;
}

function renderML() {
  return `${tabs(activeModule())}
    <h3>${state.tab}</h3>
    <div class="form-grid">
      ${selectField("model", "Model", ["Random Forest", "XGBoost", "U-Net"])}
      ${selectField("cv", "Validation", ["spatial block cross-validation", "leave-area-out"])}
      ${field("block_size", "Spatial block size (m)", "1000", false, "number")}
      ${field("ml_output", "Output folder", `${examples.output}\\ml`, true)}
      <div class="field wide">
        <label>Features without InSAR</label>
        <input id="base_features" value="slope,aspect,twi,ndvi,elevation">
      </div>
      <div class="field wide">
        <label>Features with InSAR</label>
        <input id="insar_features" value="slope,aspect,twi,ndvi,elevation,los_velocity,coherence">
      </div>
    </div>
    <button class="primary" onclick="runTool('ml', {model: val('model'), output_folder: val('ml_output')})">Run Comparison</button>
    <p class="hint">Required outputs: susceptibility_without_insar.tif, susceptibility_with_insar.tif, model_comparison.csv, feature_importance.png, shap_summary.png.</p>`;
}

function renderInterpretation() {
  return `${tabs(activeModule())}
    <h3>AI Interpretation</h3>
    <div class="field wide">
      <label>Question for SlopeGuard</label>
      <textarea id="interpret_prompt">Explain whether InSAR improved performance, which features mattered most, geomorphological plausibility, uncertainty, and next steps.</textarea>
    </div>
    <div class="form-grid">
      ${field("metrics_path", "Metrics CSV", "outputs/ml/model_comparison.csv", true)}
      ${field("interp_output", "Output folder", `${examples.output}\\interpretation`, true)}
    </div>
    <button class="primary" onclick="runTool('interpretation', {prompt: val('interpret_prompt'), output_folder: val('interp_output')})">Generate Interpretation</button>
    <p class="hint">This module writes an interpretation draft that can be reviewed before report generation.</p>`;
}

function renderReport() {
  return `${tabs(activeModule())}
    <h3>Report Generator</h3>
    <div class="form-grid">
      ${field("report_title", "Report title", "SlopeGuard AI Landslide Monitoring Report", true)}
      ${field("map_path", "Main map", "outputs/ml/susceptibility_with_insar.tif", true)}
      ${field("metrics_csv", "Metrics CSV", "outputs/ml/model_comparison.csv", true)}
      ${field("report_output", "Output folder", `${examples.output}\\report`, true)}
    </div>
    <button class="primary" onclick="runTool('report', {title: val('report_title'), output_folder: val('report_output')})">Generate Report Package</button>
    <p class="hint">Outputs: 2-page IEEE-style PDF, one-slide PDF summary, map layout, methodology summary, metrics table, and interpretation.</p>`;
}

function renderPanel() {
  const id = state.module;
  if (id === "project") return renderProject();
  if (id === "dem") return renderDEM();
  if (id === "sentinel2") return renderSentinel2();
  if (id === "insar") return renderInSAR();
  if (id === "inventory") return renderInventory();
  if (id === "stack") return renderStack();
  if (id === "ml") return renderML();
  if (id === "interpretation") return renderInterpretation();
  if (id === "report") return renderReport();
  return "";
}

function render() {
  const m = activeModule();
  renderNav();
  el("moduleTitle").textContent = m.title;
  el("panelContent").innerHTML = renderPanel();
  document.querySelectorAll(".tabs button").forEach((btn) => {
    btn.onclick = () => {
      state.tab = btn.dataset.tab;
      render();
    };
  });
}

function val(id) {
  const node = el(id);
  return node ? node.value : "";
}

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || res.statusText);
  return data;
}

async function saveProject() {
  const payload = {
    project_name: val("project_name"),
    study_area_name: val("study_area_name"),
    crs: val("crs"),
    resolution_m: Number(val("resolution_m") || 30),
    output_folder: val("output_folder"),
    aoi_vector: val("aoi_vector") || null,
  };
  const data = await api("/api/project", { method: "POST", body: JSON.stringify(payload) });
  mockLog(`Saved project configuration:\n${data.path}`);
}

async function runTool(tool, payload) {
  try {
    const job = await api(`/api/run/${tool}`, { method: "POST", body: JSON.stringify(payload) });
    state.activeJob = job.id;
    mockLog(`Started ${tool} job ${job.id}`);
    pollJob(job.id);
  } catch (err) {
    mockLog(`Error: ${err.message}`);
  }
}

function runStack() {
  let layers = [];
  try {
    layers = JSON.parse(val("layer_manifest"));
  } catch (err) {
    mockLog(`Layer manifest JSON is invalid: ${err.message}`);
    return;
  }
  runTool("stack", { layers, output_folder: val("stack_output") });
}

async function pollJob(id) {
  const job = await api(`/api/jobs/${id}`);
  updateJob(job);
  if (job.status === "running" || job.status === "queued") {
    setTimeout(() => pollJob(id), 1200);
  }
}

function updateJob(job) {
  el("jobStatus").textContent = job.status === "completed" ? "Completed" : job.status === "failed" ? "Failed" : job.status === "running" ? "Running" : "Queued";
  el("jobStatus").className = job.status || "";
  el("progressBar").style.width = `${job.progress || 0}%`;
  const lines = [`Job ${job.id}`, `Tool: ${job.tool}`, `Status: ${job.status}`, `Progress: ${job.progress}%`, `Message: ${job.message}`];
  if (job.error) lines.push(`Error:\n${job.error}`);
  el("logOutput").textContent = lines.join("\n");
  const list = el("outputFiles");
  list.innerHTML = "";
  (job.outputs || []).forEach((out) => {
    const li = document.createElement("li");
    const isPreview = /\.(png|jpg|jpeg)$/i.test(out);
    if (isPreview) {
      const btn = document.createElement("button");
      btn.className = "file-button";
      btn.textContent = `Open map: ${fileName(out)}`;
      btn.onclick = () => viewOutput(out);
      li.appendChild(btn);
    } else {
      li.textContent = out;
    }
    list.appendChild(li);
  });
  const firstPreview = (job.outputs || []).find((out) => /\.(png|jpg|jpeg)$/i.test(out));
  if (job.status === "completed" && firstPreview) viewOutput(firstPreview);
}

function mockLog(text) {
  el("logOutput").textContent = text;
}

function fileName(path) {
  return path.split(/[\\/]/).pop();
}

function viewOutput(path) {
  const img = el("rasterPreview");
  const terrain = document.querySelector(".terrain");
  img.src = `/api/file?path=${encodeURIComponent(path)}&t=${Date.now()}`;
  img.classList.add("visible");
  terrain.classList.add("hidden");
  el("previewLabel").textContent = fileName(path);
  mockLog(`Opened map preview in canvas:\n${path}`);
}

function createPreview() {
  const rasterPath = val("previewPath");
  if (!rasterPath) {
    mockLog("Paste a TIFF, PNG, or JPG path first.");
    return;
  }
  if (/\.(png|jpg|jpeg)$/i.test(rasterPath)) {
    viewOutput(rasterPath);
    return;
  }
  runTool("preview", { raster_path: rasterPath });
}

el("refreshJobs").onclick = async () => {
  const jobs = await api("/api/jobs");
  if (!jobs.length) return mockLog("No jobs yet.");
  updateJob(jobs[0]);
};

el("toggleJobDetails").onclick = () => {
  state.detailsOpen = !state.detailsOpen;
  el("jobDetails").classList.toggle("hidden", !state.detailsOpen);
  el("toggleJobDetails").textContent = state.detailsOpen ? "Hide" : "Details";
};

el("toggleOutputs").onclick = () => {
  state.outputsOpen = !state.outputsOpen;
  el("outputFiles").classList.toggle("visible", state.outputsOpen);
};

function runSplashSequence() {
  const steps = [
    "Loading project configuration...",
    "Checking geospatial dependencies...",
    "Preparing raster workspace...",
    "Starting SlopeGuard AI..."
  ];
  let currentStep = 0;
  const loadingText = el("splashLoadingText");
  const splashScreen = el("splashScreen");
  const appContainer = el("app");

  const interval = setInterval(() => {
    currentStep++;
    if (currentStep < steps.length) {
      loadingText.textContent = steps[currentStep];
    } else {
      clearInterval(interval);
      setTimeout(() => {
        splashScreen.classList.add("hidden");
        appContainer.classList.remove("hidden");
        
        // After transition is done, remove splash screen from DOM to prevent interaction blocking
        setTimeout(() => {
          splashScreen.style.display = "none";
        }, 800);
      }, 500);
    }
  }, 600); // Wait 600ms per step
}

render();
runSplashSequence();
