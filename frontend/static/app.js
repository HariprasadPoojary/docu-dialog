const apiBase = "/api/v1";
const form = document.querySelector("#create-project-form");
const projectList = document.querySelector("#project-list");
const projectCount = document.querySelector("#project-count");
const notice = document.querySelector("#notice");
const selectedPanel = document.querySelector("#selected-project");
let projects = [];
let selectedProjectId = null;

function showNotice(message, isSuccess = false) {
  notice.textContent = message;
  notice.classList.toggle("success", isSuccess);
  notice.hidden = false;
}

function hideNotice() {
  notice.hidden = true;
  notice.textContent = "";
}

async function request(path, options = {}) {
  const headers = { ...options.headers };
  if (!(options.body instanceof FormData)) headers["Content-Type"] = "application/json";
  const response = await fetch(`${apiBase}${path}`, { ...options, headers });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${response.status})`);
  }
  if (response.status === 204) return null;
  return response.json();
}

function renderSelectedProject(project) {
  selectedPanel.hidden = !project;
  if (!project) {
    selectedPanel.replaceChildren();
    return;
  }

  selectedPanel.dataset.projectId = project.id;
  const title = document.createElement("h2");
  title.textContent = project.name;
  const description = document.createElement("p");
  description.textContent = project.description || "No description added.";

  const documentHeading = document.createElement("div");
  documentHeading.className = "document-heading";
  const documentTitle = document.createElement("h3");
  documentTitle.textContent = "Project documents";
  documentHeading.append(documentTitle);

  const uploadForm = document.createElement("form");
  uploadForm.id = "upload-documents-form";
  uploadForm.className = "upload-form";
  const fileInput = document.createElement("input");
  fileInput.type = "file";
  fileInput.name = "files";
  fileInput.multiple = true;
  fileInput.accept = ".pdf,.docx,.txt,.md,.csv";
  fileInput.required = true;
  fileInput.setAttribute("aria-label", "Choose documents to upload");
  const uploadButton = document.createElement("button");
  uploadButton.type = "submit";
  uploadButton.className = "primary-button";
  uploadButton.textContent = "Upload files";
  uploadForm.append(fileInput, uploadButton);

  const uploadNote = document.createElement("p");
  uploadNote.className = "upload-note";
  uploadNote.textContent = "PDF, DOCX, TXT, Markdown, or CSV · up to 10 files, 20 MB each, 50 MB total. Uploaded files will be indexed in a later step.";

  const documentItems = document.createElement("div");
  documentItems.className = "document-items";
  documentItems.id = "document-items";
  documentItems.innerHTML = '<p class="document-empty">Loading documents…</p>';
  selectedPanel.replaceChildren(title, description, documentHeading, uploadForm, uploadNote, documentItems);
  void loadDocuments(project.id);
}

function renderDocuments(projectId, documents) {
  if (selectedPanel.dataset.projectId !== projectId) return;
  const list = selectedPanel.querySelector("#document-items");
  if (!list) return;
  list.replaceChildren();
  if (documents.length === 0) {
    const empty = document.createElement("p");
    empty.className = "document-empty";
    empty.textContent = "No documents uploaded to this project yet.";
    list.append(empty);
    return;
  }

  for (const documentItem of documents) {
    const row = document.createElement("article");
    row.className = "document-row";
    const info = document.createElement("div");
    info.className = "document-info";
    const filename = document.createElement("span");
    filename.className = "document-filename";
    filename.textContent = documentItem.original_filename;
    const metadata = document.createElement("span");
    metadata.className = "document-meta";
    metadata.textContent = `${formatBytes(documentItem.size_bytes)} · ${documentItem.status}`;
    info.append(filename, metadata);

    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "delete-button";
    remove.textContent = "Remove";
    remove.setAttribute("aria-label", `Remove ${documentItem.original_filename}`);
    remove.addEventListener("click", () => deleteDocument(projectId, documentItem));
    row.append(info, remove);
    list.append(row);
  }
}

function formatBytes(size) {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function renderProjects() {
  projectCount.textContent = String(projects.length);
  if (!projects.some((project) => project.id === selectedProjectId)) {
    selectedProjectId = projects[0]?.id ?? null;
  }

  if (projects.length === 0) {
    projectList.innerHTML = '<p class="empty-state">No projects yet. Create one to get started.</p>';
    renderSelectedProject(null);
    return;
  }

  projectList.replaceChildren();
  for (const project of projects) {
    const row = document.createElement("article");
    row.className = `project-row${project.id === selectedProjectId ? " selected" : ""}`;

    const select = document.createElement("button");
    select.type = "button";
    select.className = "project-select";
    select.setAttribute("aria-pressed", String(project.id === selectedProjectId));
    const name = document.createElement("span");
    name.className = "project-name";
    name.textContent = project.name;
    const description = document.createElement("span");
    description.className = "project-description";
    description.textContent = project.description || "Select to view this project";
    select.append(name, description);
    select.addEventListener("click", () => {
      selectedProjectId = project.id;
      renderProjects();
    });

    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "delete-button";
    remove.textContent = "Delete";
    remove.setAttribute("aria-label", `Delete ${project.name}`);
    remove.addEventListener("click", () => deleteProject(project));

    row.append(select, remove);
    projectList.append(row);
  }

  renderSelectedProject(projects.find((project) => project.id === selectedProjectId));
}

async function loadProjects() {
  projectList.innerHTML = '<p class="empty-state">Loading projects…</p>';
  try {
    projects = await request("/projects");
    hideNotice();
    renderProjects();
  } catch (error) {
    projectList.innerHTML = '<p class="empty-state">Projects could not be loaded.</p>';
    renderSelectedProject(null);
    showNotice(error.message);
  }
}

async function loadDocuments(projectId) {
  try {
    const documents = await request(`/projects/${projectId}/documents`);
    renderDocuments(projectId, documents);
  } catch (error) {
    if (selectedPanel.dataset.projectId !== projectId) return;
    const list = selectedPanel.querySelector("#document-items");
    if (list) list.textContent = error.message;
  }
}

async function deleteProject(project) {
  if (!window.confirm(`Delete “${project.name}”? Its documents and stored files will also be removed.`)) return;
  try {
    await request(`/projects/${project.id}`, { method: "DELETE" });
    projects = projects.filter((item) => item.id !== project.id);
    hideNotice();
    renderProjects();
    showNotice("Project deleted.", true);
  } catch (error) {
    showNotice(error.message);
  }
}

async function deleteDocument(projectId, documentItem) {
  if (!window.confirm(`Remove “${documentItem.original_filename}” from this project?`)) return;
  try {
    await request(`/projects/${projectId}/documents/${documentItem.id}`, { method: "DELETE" });
    hideNotice();
    await loadDocuments(projectId);
    showNotice("Document removed.", true);
  } catch (error) {
    showNotice(error.message);
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const submitButton = form.querySelector("button[type='submit']");
  submitButton.disabled = true;
  hideNotice();
  const formData = new FormData(form);
  try {
    const project = await request("/projects", {
      method: "POST",
      body: JSON.stringify({
        name: formData.get("name"),
        description: formData.get("description") || null,
      }),
    });
    projects = [project, ...projects];
    selectedProjectId = project.id;
    form.reset();
    renderProjects();
    showNotice("Project created.", true);
  } catch (error) {
    showNotice(error.message);
  } finally {
    submitButton.disabled = false;
  }
});

selectedPanel.addEventListener("submit", async (event) => {
  if (event.target.id !== "upload-documents-form") return;
  event.preventDefault();
  const projectId = selectedPanel.dataset.projectId;
  const uploadForm = event.target;
  const uploadButton = uploadForm.querySelector("button[type='submit']");
  const fileInput = uploadForm.querySelector("input[type='file']");
  if (!fileInput.files.length) return;

  uploadButton.disabled = true;
  hideNotice();
  const body = new FormData();
  for (const file of fileInput.files) body.append("files", file);
  try {
    await request(`/projects/${projectId}/documents`, { method: "POST", body });
    uploadForm.reset();
    await loadDocuments(projectId);
    showNotice("Documents uploaded and queued for indexing.", true);
  } catch (error) {
    showNotice(error.message);
  } finally {
    uploadButton.disabled = false;
  }
});

document.querySelector("#refresh-projects").addEventListener("click", loadProjects);
loadProjects();
